import os

c.JupyterHub.port = 8080

c.JupyterHub.hub_ip = '0.0.0.0'
c.JupyterHub.hub_port = 8081

c.JupyterHub.proxy_api_port = 8082

c.JupyterHub.spawner_class = 'kubespawner.KubeSpawner'

c.KubeSpawner.port = 8080

c.KubeSpawner.hub_connect_ip = os.environ.get('JUPYTERHUB_SERVICE_NAME', 'jupyterhub')
c.KubeSpawner.hub_connect_port = 8080

c.KubeSpawner.http_timeout = 60

c.KubeSpawner.singleuser_image_spec = os.environ.get('JUPYTERHUB_NOTEBOOK_IMAGE',
        'minimal-notebook:3.5')

c.KubeSpawner.singleuser_uid = os.getuid()
c.KubeSpawner.singleuser_fs_gid = os.getuid()

c.KubeSpawner.cmd = ['jupyterhub-singleuser']
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
