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

service_name = os.environ.get('JUPYTERHUB_SERVICE_NAME', 'jupyterhub')

c.JupyterHub.port = 8080

c.JupyterHub.hub_ip = '0.0.0.0'
c.JupyterHub.hub_port = 8081

c.JupyterHub.proxy_api_port = 8082

c.Spawner.start_timeout = 120
c.Spawner.http_timeout = 60

c.KubeSpawner.port = 8080

c.KubeSpawner.hub_connect_ip = service_name
c.KubeSpawner.hub_connect_port = 8080

# JupyterHub < 0.9.
c.KubeSpawner.singleuser_extra_labels = { 'app': service_name }

# JupyterHub >= 0.9.
c.KubeSpawner.common_labels = { 'app': service_name }

c.KubeSpawner.singleuser_uid = os.getuid()
c.KubeSpawner.singleuser_fs_gid = os.getuid()

c.KubeSpawner.singleuser_extra_annotations = {
    "alpha.image.policy.openshift.io/resolve-names": "*"
}

c.KubeSpawner.cmd = ['start-singleuser.sh']

c.KubeSpawner.args = ['--hub-api-url=http://%s:%d/hub/api' % (
        c.KubeSpawner.hub_connect_ip, c.KubeSpawner.hub_connect_port)]

c.KubeSpawner.pod_name_template = '%s-nb-{username}' % c.KubeSpawner.hub_connect_ip

c.JupyterHub.admin_access = True

if os.environ.get('JUPYTERHUB_COOKIE_SECRET'):
    c.JupyterHub.cookie_secret = os.environ[
            'JUPYTERHUB_COOKIE_SECRET'].encode('UTF-8')
else:
    c.JupyterHub.cookie_secret_file = '/opt/app-root/data/cookie_secret'

if os.environ.get('JUPYTERHUB_DATABASE_PASSWORD'):
    c.JupyterHub.db_url = 'postgresql://jupyterhub:%s@%s:5432/jupyterhub' % (
            os.environ['JUPYTERHUB_DATABASE_PASSWORD'],
            os.environ['JUPYTERHUB_DATABASE_HOST'])
else:
    c.JupyterHub.db_url = '/opt/app-root/data/database.sqlite'

c.JupyterHub.authenticator_class = 'tmpauthenticator.TmpAuthenticator'

c.JupyterHub.spawner_class = 'kubespawner.KubeSpawner'

c.KubeSpawner.singleuser_image_spec = os.environ.get('JUPYTERHUB_NOTEBOOK_IMAGE',
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
