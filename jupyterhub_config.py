import os

# Helper functions for doing conversions or translations if needed.

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

# Define the default configuration for JupyterHub application.

application_name = os.environ.get('APPLICATION_NAME', 'jupyterhub')
application_name = os.environ.get('JUPYTERHUB_SERVICE_NAME', application_name)

c.JupyterHub.port = 8080

c.JupyterHub.hub_ip = '0.0.0.0'
c.JupyterHub.hub_port = 8081

c.ConfigurableHTTPProxy.api_url = 'http://127.0.0.1:8082'

c.Spawner.start_timeout = 120
c.Spawner.http_timeout = 60

c.KubeSpawner.port = 8080

c.JupyterHub.hub_connect_ip = application_name

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

c.KubeSpawner.image_spec = os.environ.get('JUPYTERHUB_NOTEBOOK_IMAGE',
        's2i-minimal-notebook:3.5')

if os.environ.get('JUPYTERHUB_NOTEBOOK_MEMORY'):
    c.Spawner.mem_limit = convert_size_to_bytes(os.environ['JUPYTERHUB_NOTEBOOK_MEMORY'])

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
