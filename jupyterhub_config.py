import os

import wrapt

from kubernetes.client.rest import ApiException

from kubernetes.client.configuration import Configuration
from kubernetes.config.incluster_config import load_incluster_config
from kubernetes.client.api_client import ApiClient
from openshift.dynamic import DynamicClient

# Helper function for doing unit conversions or translations if needed.

def convert_size_to_bytes(size):
    multipliers = {
        'k': 1000,
        'm': 1000**2,
        'g': 1000**3,
        't': 1000**4,
        'ki': 1024,
        'mi': 1024**2,
        'gi': 1024**3,
        'ti': 1024**4,
    }

    size = str(size)

    for suffix in multipliers:
        if size.lower().endswith(suffix):
            return int(size[0:-len(suffix)]) * multipliers[suffix]
    else:
        if size.lower().endswith('b'):
            return int(size[0:-1])

    try:
        return int(size)
    except ValueError:
        raise RuntimeError('"%s" is not a valid memory specification. Must be an integer or a string with suffix K, M, G, T, Ki, Mi, Gi or Ti.' % size)

# Work out the name of the namespace in which we are being deployed.
# deployment is in.

service_account_path = '/var/run/secrets/kubernetes.io/serviceaccount'

with open(os.path.join(service_account_path, 'namespace')) as fp:
    namespace = fp.read().strip()

# Initialise client for the REST API used doing configuration.
#
# XXX Currently have a workaround here for OpenShift 4.0 beta versions
# which disables verification of the certificate. If don't use this the
# Python openshift/kubernetes clients will fail. We also disable any
# warnings from urllib3 to get rid of the noise in the logs this creates.

load_incluster_config()

import urllib3
urllib3.disable_warnings()
instance = Configuration()
instance.verify_ssl = False
Configuration.set_default(instance)

api_client = DynamicClient(ApiClient())

image_stream_resource = api_client.resources.get(
     api_version='image.openshift.io/v1', kind='ImageStream')

# Helper function for determining the correct name for the image. We
# need to do this for references to image streams because of the image
# lookup policy often not being correctly setup on OpenShift clusters.

def resolve_image_name(name):
    # If the image name contains a slash, we assume it is already
    # referring to an image on some image registry. Even if it does
    # not contain a slash, it may still be hosted on docker.io.

    if name.find('/') != -1:
        return name

    # Separate actual source image name and tag for the image from the
    # name. If the tag is not supplied, default to 'latest'.

    parts = name.split(':', 1)

    if len(parts) == 1:
        source_image, tag = parts, 'latest'
    else:
        source_image, tag = parts

    # See if there is an image stream in the current project with the
    # target name.

    try:
        image_stream = image_stream_resource.get(namespace=namespace,
                name=source_image)

    except ApiException as e:
        if e.status not in (403, 404):
            raise

        return name

    # If we get here then the image stream exists with the target name.
    # We need to determine if the tag exists. If it does exist, we
    # extract out the full name of the image including the reference
    # to the image registry it is hosted on.

    if image_stream.status.tags:
        for entry in image_stream.status.tags:
            if entry.tag == tag:
                registry_image = image_stream.status.dockerImageRepository
                if registry_image:
                    return '%s:%s' % (registry_image, tag)

    # Use original value if can't find a matching tag.

    return name

# Define the default configuration for JupyterHub application. The
# JUPYTERHUB_SERVICE_NAME is kept for backward compatibility only, use
# APPLICATION_NAME to pass in the name of the deployment.

application_name = os.environ.get('APPLICATION_NAME', 'jupyterhub')
application_name = os.environ.get('JUPYTERHUB_SERVICE_NAME', application_name)

c.JupyterHub.port = 8080

c.JupyterHub.hub_ip = '0.0.0.0'
c.JupyterHub.hub_port = 8081

c.JupyterHub.hub_connect_ip = application_name

c.ConfigurableHTTPProxy.api_url = 'http://127.0.0.1:8082'

c.Spawner.start_timeout = 120
c.Spawner.http_timeout = 60

c.KubeSpawner.port = 8080

c.KubeSpawner.common_labels = { 'app': application_name }

c.KubeSpawner.uid = os.getuid()
c.KubeSpawner.fs_gid = os.getuid()

c.KubeSpawner.extra_annotations = {
    "alpha.image.policy.openshift.io/resolve-names": "*"
}

c.KubeSpawner.cmd = ['start-singleuser.sh']

c.KubeSpawner.pod_name_template = '%s-nb-{username}' % application_name

c.JupyterHub.admin_access = True

if os.environ.get('JUPYTERHUB_COOKIE_SECRET'):
    c.JupyterHub.cookie_secret = os.environ[
            'JUPYTERHUB_COOKIE_SECRET'].encode('UTF-8')
else:
    c.JupyterHub.cookie_secret_file = '/opt/app-root/data/cookie_secret'

if os.environ.get('JUPYTERHUB_DATABASE_PASSWORD'):
    c.JupyterHub.db_url = 'postgresql://jupyterhub:%s@%s:5432/%s' % (
            os.environ['JUPYTERHUB_DATABASE_PASSWORD'],
            os.environ['JUPYTERHUB_DATABASE_HOST'],
            os.environ.get('JUPYTERHUB_DATABASE_NAME', 'jupyterhub'))
else:
    c.JupyterHub.db_url = '/opt/app-root/data/database.sqlite'

c.JupyterHub.authenticator_class = 'tmpauthenticator.TmpAuthenticator'

c.JupyterHub.spawner_class = 'kubespawner.KubeSpawner'

c.KubeSpawner.image_spec = resolve_image_name(
        os.environ.get('JUPYTERHUB_NOTEBOOK_IMAGE',
        's2i-minimal-notebook:3.6'))

if os.environ.get('JUPYTERHUB_NOTEBOOK_MEMORY'):
    c.Spawner.mem_limit = convert_size_to_bytes(os.environ['JUPYTERHUB_NOTEBOOK_MEMORY'])

# Workaround bug in minishift where a service cannot be contacted from a
# pod which backs the service. For further details see the minishift issue
# https://github.com/minishift/minishift/issues/2400.
#
# What these workarounds do is monkey patch the JupyterHub proxy client
# API code, and the code for creating the environment for local service
# processes, and when it sees something which uses the service name as
# the target in a URL, it replaces it with localhost. These work because
# the proxy/service processes are in the same pod. It is not possible to
# change hub_connect_ip to localhost because that is passed to other
# pods which need to contact back to JupyterHub, and so it must be left
# as the service name.

@wrapt.patch_function_wrapper('jupyterhub.proxy', 'ConfigurableHTTPProxy.add_route')
def _wrapper_add_route(wrapped, instance, args, kwargs):
    def _extract_args(routespec, target, data, *_args, **_kwargs):
        return (routespec, target, data, _args, _kwargs)

    routespec, target, data, _args, _kwargs = _extract_args(*args, **kwargs)

    old = 'http://%s:%s' % (c.JupyterHub.hub_connect_ip, c.JupyterHub.hub_port)
    new = 'http://127.0.0.1:%s' % c.JupyterHub.hub_port

    if target.startswith(old):
        target = target.replace(old, new)

    return wrapped(routespec, target, data, *_args, **_kwargs)

@wrapt.patch_function_wrapper('jupyterhub.spawner', 'LocalProcessSpawner.get_env')
def _wrapper_get_env(wrapped, instance, args, kwargs):
    env = wrapped(*args, **kwargs)

    target = env.get('JUPYTERHUB_API_URL')

    old = 'http://%s:%s' % (c.JupyterHub.hub_connect_ip, c.JupyterHub.hub_port)
    new = 'http://127.0.0.1:%s' % c.JupyterHub.hub_port

    if target and target.startswith(old):
        target = target.replace(old, new)
        env['JUPYTERHUB_API_URL'] = target

    return env

# Load configuration included in the image.

image_config_file = '/opt/app-root/src/.jupyter/jupyterhub_config.py'

if os.path.exists(image_config_file):
    with open(image_config_file) as fp:
        exec(compile(fp.read(), image_config_file, 'exec'), globals())

# Load configuration provided via the environment.

environ_config_file = '/opt/app-root/configs/jupyterhub_config.py'

if os.path.exists(environ_config_file):
    with open(environ_config_file) as fp:
        exec(compile(fp.read(), environ_config_file, 'exec'), globals())
