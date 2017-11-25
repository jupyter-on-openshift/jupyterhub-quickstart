import os

c.JupyterHub.port = 8080

c.JupyterHub.hub_ip = '0.0.0.0'
c.JupyterHub.hub_port = 8081

c.JupyterHub.proxy_api_port = 8082

c.JupyterHub.spawner_class = 'kubespawner.KubeSpawner'

c.Spawner.http_timeout = 60

c.Spawner.singleuser_image_spec = os.get('JUPYTERHUB_NOTEBOOK_IMAGE',
        'minimal-notebook:3.5')

c.Spawner.singleuser_uid = os.getuid()
c.Spawner.singleuser_fs_gid = os.getuid()

c.Spawner.port = 8080

c.Spawner.hub_connect_ip = os.environ['JUPYTERHUB_SERVICE_HOST']
c.Spawner.hub_connect_port = 8080

c.Spawner.cmd = ['jupyterhub-singleuser']
c.Spawner.args = ['--hub-api-url=http://%s:%d/hub/api' % (
        c.Spawner.hub_connect_ip, c.Spawner.hub_connect_port)]

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

c.JupyterHub.authenticator_class = 'hashauthenticator.HashAuthenticator'
c.HashAuthenticator.secret_key = os.environ.get(
        'JUPYTERHUB_AUTHENTICATION_KEY', 'jupyterhub')

whitelist = os.environ.get('JUPYTERHUB_USER_WHITELIST', '').strip()
whitelist = whitelist and whitelist.split() or []

c.Authenticator.whitelist = set(whitelist)

admin_users = os.environ.get('JUPYTERHUB_ADMIN_USERS', '').strip()
admin_users = admin_users and admin_users.split() or []

c.Authenticator.admin_users = set(admin_users)
