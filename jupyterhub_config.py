import os

from kubespawner import KubeSpawner
from traitlets import default, Unicode, List

service_name = os.environ.get('JUPYTERHUB_SERVICE_NAME', 'jupyterhub')

c.JupyterHub.port = 8080

c.JupyterHub.hub_ip = '0.0.0.0'
c.JupyterHub.hub_port = 8081

c.JupyterHub.proxy_api_port = 8082

c.KubeSpawner.port = 8080

c.KubeSpawner.hub_connect_ip = service_name
c.KubeSpawner.hub_connect_port = 8080

c.KubeSpawner.http_timeout = 60

c.KubeSpawner.singleuser_extra_labels = { 'app': service_name }

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

class KubeProfileSpawner(KubeSpawner):

    profiles = List(
        trait = Unicode(),
        default_value = ['minimal-notebook:3.5'],
        minlen = 1,
        config = True,
        help = "Profiles for images available to deploy."
    )

    form_template = Unicode("""
        <label for="profile">Select an image profile:</label>
        <select class="form-control" name="profile" required autofocus>
            {option_template}
        </select>""",
        config = True, help = "Form template."
    )

    option_template = Unicode("""
        <option value="{profile}">{profile}</option>""",
        config = True, help = "Template for html form options."
    )

    @default('options_form')
    def _options_form(self):
        """Return the form with the drop-down menu."""
        options = ''.join([
            self.option_template.format(profile=di) for di in self.profiles
        ])
        return self.form_template.format(option_template=options)

    def options_from_form(self, formdata):
        """Parse the submitted form data and turn it into the correct
           structures for self.user_options."""

        formdata = dict(super(KubeProfileSpawner,
                self).options_from_form(formdata))

        default = self.profiles[0]
        profile = formdata.get('profile', [default])[0]

        if profile not in self.profiles:
            profile = default

        formdata.update(dict(profile=profile))

        return formdata

    def start(self):
        self.singleuser_image_spec = self.user_options['profile']
        return super(KubeProfileSpawner, self).start()

notebook_images = [name.strip() for name in
        os.environ.get('JUPYTERHUB_NOTEBOOK_IMAGE',
	'minimal-notebook:3.5').split(',')]

if len(notebook_images) == 1:
    c.KubeSpawner.singleuser_image_spec = notebook_images[0]
    c.JupyterHub.spawner_class = KubeSpawner
else:
    c.KubeProfileSpawner.profiles = notebook_images
    c.JupyterHub.spawner_class = KubeProfileSpawner

# Load configuration included in the image.

image_config_file = '/opt/app-root/src/jupyterhub_config.py'

if os.path.exists(image_config_file):
    with open(image_config_file) as fp:
        exec(compile(fp.read(), image_config_file, 'exec'), globals())

# Load configuration provided via the environment.

environ_config_file = '/opt/app-root/configs/jupyterhub_config.py'

if os.path.exists(environ_config_file):
    with open(environ_config_file) as fp:
        exec(compile(fp.read(), environ_config_file, 'exec'), globals())
