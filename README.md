JupyterHub for OpenShift
========================

This repository contains software to make it easier to host Jupyter Notebooks on OpenShift using JupyterHub.

OpenShift, being a Kubernetes distribution, you can use the  [JupyterHub deployment method for Kubernetes](http://zero-to-jupyterhub.readthedocs.io/) created by the Jupyter project team. That deployment method relies on using Helm templates to manage deployment. The use of Helm, and that Kubernetes is a platform for IT operations, means it isn't as easy to deploy by end users as it could be. This repository aims to provide a much easier way of deploying JupyterHub to OpenShift which makes better use of OpenShift specific features, including OpenShift templates, and Source-to-Image (S2I) builders. The result is a method for deploying JupyterHub to OpenShift which doesn't require any special admin privileges to the underlying Kubernetes cluster, or OpenShift. As long as a user has the necessary quotas for memory, CPU and persistent storage, they can deploy JupyterHub themselves.

Preparing the Jupyter Images
----------------------------

The first step in deploying JupyterHub is to prepare the notebook images and the image for JupyterHub.

You can use the official Jupyter project ``docker-stacks`` images, but some extra configuration is required to use those as they will not work out of the box with OpenShift. Details on how to use the Jupyter project images is described later.

To create a minimal Jupyter notebook image, as well as images similar to the ``scipy-notebook`` and ``tensorflow-notebook`` images provided by the Jupyter project team, run:

```
oc create -f https://raw.githubusercontent.com/jupyter-on-openshift/jupyter-notebooks/master/images.json
```

This will create a build configuration in your OpenShift project to build the images using the Python 3.5 S2I builder. You can watch the progress of the build for the minimal Jupyter notebook image by running:

```
oc logs --follow bc/s2i-minimal-notebook
```

A tagged image ``s2i-minimal-notebook:3.5`` should be created in your project.

For more detailed instructions on creating the minimal Jupyter notebook image, and how to create custom notebook images, read:

* https://github.com/jupyter-on-openshift/jupyter-notebooks

To create the JupyterHub image, next run:

```
oc create -f https://raw.githubusercontent.com/jupyter-on-openshift/jupyterhub-quickstart/master/images.json
```

This will create a build configuration in your OpenShift project to build a JupyterHub image using the Python 3.5 S2I builder. You can watch the progress of the build by running:

```
oc logs --follow bc/jupyterhub
```

A tagged image ``jupyterhub:latest`` should be created in your project.

Loading the JupyterHub Templates
--------------------------------

To make it easier to deploy JupyterHub in OpenShift, templates are provided. To load the templates run:

```
oc create -f https://raw.githubusercontent.com/jupyter-on-openshift/jupyterhub-quickstart/master/templates.json
```

Creating the JupyterHub Deployment
----------------------------------

To deploy JupyterHub with the default configuration, which will provide you a deployment similar to ``tmpnb.org``, and using the ``s2i-minimal-notebook:3.5`` image, run:

```
oc new-app --template jupyterhub-deployer
```

This deployment requires a single persistent volume of size 1Gi for use by the PostgreSQL database deployed along with JupyterHub. The notebooks which will be deployed will use ephemeral storage.

To monitor progress as the deployment occurs run:

```
oc rollout status dc/jupyterhub
```

To view the hostname assigned to the JupyterHub instance by OpenShift, run:

```
oc get route/jupyterhub
```

Access the host from a browser and a Jupyter notebook instance will be automatically started for you. Access the site using a different browser, or from a different computer, and you should get a second Jupyter notebook instance, separate to the first.

To see a list of the pods corresponding to the notebook instances, run:

```
oc get pods --selector app=jupyterhub,component=singleuser-server
```

This should yield results similar to:

```
NAME                                                         READY     STATUS    RESTARTS   AGE
jupyterhub-nb-5b7eac5d-2da834-2d4219-2dac19-2dad7f2ee00e30   1/1       Running   0          5m
```

As this configuration doesn't provide access to the admin panel in JupyterHub, you can forcibly stop a notebook instance by running ``oc delete pod`` on the specific pod instance.

To delete the JupyterHub instance along with all notebook instances, run:

```
oc delete all,configmap,pvc,serviceaccount,rolebinding --selector app=jupyterhub
```

Deploying with a Custom Notebook Image
--------------------------------------

To deploy JupyterHub and have it build a custom notebook image for you, run:

```
oc new-app --template jupyterhub-quickstart \
  --param APPLICATION_NAME=jakevdp \
  --param GIT_REPOSITORY_URL=https://github.com/jakevdp/PythonDataScienceHandbook
```

Note that the notebook image will be built in parallel to JupyterHub being deployed. You will need to wait until the build of the image has completed before you can visit JupyterHub the first time. You can monitor the build of the image using the command:

```
oc logs bc/jakevdp-nb --follow
```

To deploy JupyterHub using a custom notebook image you had already created, run:

```
oc new-app --template jupyterhub-deployer \
  --param APPLICATION_NAME=jakevdp \
  --param NOTEBOOK_IMAGE=jakevdp-notebook:latest
```

Because ``APPLICATION_NAME`` was supplied, the JupyterHub instance and notebooks in this case will all be labelled with ``jakevdp``.

To get the hostname assigned for the JupyterHub instance, run:

```
oc get route/jakevdp
```

To delete the JupyterHub instance along with all notebook instances, run:

```
oc delete all,configmap,pvc,serviceaccount,rolebinding --selector app=jakevdp
```

Using the OpenShift Web Console
-------------------------------

JupyterHub can also be deployed from the web console by selecting _Select from Project_ from the _Add to Project_ menu, filtering on _jupyter_ and choosing the appropriate template.

Customising the JupyterHub Deployment
-------------------------------------

JupyterHub, and how notebook images are deployed, can be customised through a ``jupyterhub_config.py`` file. The JupyterHub image created from this repository has a default version of this file which sets a number of defaults required for running JupyterHub in OpenShift. You can provide your own customisations, including overriding any defaults, in a couple of ways.

The first is that when using the supplied templates to deploy JupyterHub, you can provide your own configuration through the ``JUPYTERHUB_CONFIG`` template parameter. This configuration will be read after the default configuration, with any settings being merged with the existing settings.

The second is to use the JupyterHub image built from this repository as an S2I builder, to incorporate your own ``jupyterhub_config.py`` file from a hosted Git repository, or local directory if using a binary input build. This will be merged with the default settings before any configuration supplied via ``JUPYTERHUB_CONFIG`` when using a template to deploy the JupyterHub image.

When using an S2I build, the repository can include any additional files to be incorporated into the JupyterHub image which may be needed for your customisations. This includes being able to supply a ``requirements.txt`` file for additional Python packages to be installed, as may be required by an authenticator to be used with JupyterHub.

To illustrate overriding the configuration when deploying JupyterHub using the quick start template, create a local file ``jupyterhub_config.py`` which contains:

```
c.KubeSpawner.start_timeout = 180
c.KubeSpawner.http_timeout = 120
```

Deploy JupyterHub using the quick start template as was done previously, but this time set the ``JUPYTERHUB_CONFIG`` template parameter.

```
oc new-app --template jupyterhub-quickstart \
  --param APPLICATION_NAME=jakevdp \
  --param GIT_REPOSITORY_URL=https://github.com/jakevdp/PythonDataScienceHandbook \
  --param JUPYTERHUB_CONFIG="`cat jupyterhub_config.py`"
```

If you need to edit the configuration after the deployment has been made, you can edit the config map which was created:

```
oc edit configmap/jakevdp-cfg
```

JupyterHub only reads the configuration on startup, so trigger a new deployment of JupyterHub.

```
oc rollout latest dc/jakevdp
```

Note that triggering a new deployment will result in any running notebook instances being shutdown, and users will need to start up a new notebook instance through the JupyterHub interface.

Providing a Selection of Images to Deploy
-----------------------------------------

When deploying JupyterHub using the templates, the ``NOTEBOOK_IMAGE`` template parameter is used to specify the name of the image which is to be deployed when starting an instance for a user. If you want to provide users a choice of images you will need to set ``wrapspawner.ProfilesSpawner`` as the spawner class for JupyterHub and provide a list of the image choices, in the JupyterHub configuration. The list of images will be presented in a drop down menu when the user requests a notebook instance be started through the JupyterHub web interface.

Note that the ``wrapspawner`` package is installed by default, so you do not need to use the S2I build method to create a custom JupyterHub image.

```
c.JupyterHub.spawner_class = 'wrapspawner.ProfilesSpawner'

c.ProfilesSpawner.profiles = [
    (
        "Minimal Notebook (CentOS 7 / Python 3.5)",
        's2i-minimal-notebook',
        'kubespawner.KubeSpawner',
        dict(singleuser_image_spec='s2i-minimal-notebook:3.5')
    ),
    (
        "SciPy Notebook (CentOS 7 / Python 3.5)",
        's2i-scipy-notebook',
        'kubespawner.KubeSpawner',
        dict(singleuser_image_spec='s2i-scipy-notebook:3.5')
    ),
    (
        "Tensorflow Notebook (CentOS 7 / Python 3.5)",
        's2i-tensorflow-notebook',
        'kubespawner.KubeSpawner',
        dict(singleuser_image_spec='s2i-tensorflow-notebook:3.5')
    )
]
```

This will override any image defined by the ``NOTEBOOK_IMAGE`` template parameter.

The first value in the tuple for an image is the display name. The second value is a unique key identifying the selection. The third value should always be ``kubespawner.KubeSpawner``. The final value is a dictionary with the settings to be applied to the spawner when deploying the image.

In this case, the ``singleuser_image_spec`` setting should be set to the name for the deployed image. The name of the image should be the name of the image stream in the same project JupyterHub is deployed, including an image tag if not ``latest``, or can be the full image name identifying an image on a remote image registry.

This dictionary can be used to set other per image specific settings if required.

When multiple choices are available, the user can still only have one notebook instance running at a time. If they want to switch which image they are using, they need to use the _Control Panel_ in the JupyterHub web interface to stop the existing notebook instance. They can then start a new instance with a different image.

Note that there is currently an issue with JupyterHub when using ``wrapspawner.ProfilesSpawner``. This will prevent you accessing a server of another user as an admin from the Jupyter admin control panel. Details of this issue can be found at:

* https://github.com/jupyterhub/jupyterhub/issues/1629

Using the Jupyter Project Notebook Images
-----------------------------------------

The official Jupyter Project notebook images:

* jupyter/base-notebook
* jupyter/r-notebook
* jupyter/minimal-notebook
* jupyter/scipy-notebook
* jupyter/tensorflow-notebook
* jupyter/datascience-notebook
* jupyter/pyspark-notebook
* jupyter/all-spark-notebook

will not work out of the box with OpenShift. This is because they have not been designed to work with an arbitrarily assigned user ID without additional configuration. The images are also very large and the size exceeds what can be deployed to hosted OpenShift environments such as OpenShift Online.

If you still want to run the official Jupyter Project notebook images, you can, but you will need to supply additional configuration to the ``KubeSpanwer`` plugin for these images to have them work. For example:

```
c.JupyterHub.spawner_class = 'wrapspawner.ProfilesSpawner'

c.ProfilesSpawner.profiles = [
    (
        "Jupyter Project - Minimal Notebook",
        'minimal-notebook',
        'kubespawner.KubeSpawner',
        dict(singleuser_image_spec='docker.io/jupyter/minimal-notebook:latest',
             singleuser_supplemental_gids=[100])
    ),
    (
        "Jupyter Project - SciPy Notebook",
        'scipy-notebook',
        'kubespawner.KubeSpawner',
        dict(singleuser_image_spec='docker.io/jupyter/scipy-notebook:latest',
             singleuser_supplemental_gids=[100])
    ),
    (
        "Jupyter Project - DataScience Notebook",
        'datascience-notebook',
        'kubespawner.KubeSpawner',
        dict(singleuser_image_spec='docker.io/jupyter/datascience-notebook:latest',
             singleuser_supplemental_gids=[100])
    ),
    (
        "Jupyter Project - Tensorflow Notebook",
        'tensorflow-notebook',
        'kubespawner.KubeSpawner',
        dict(singleuser_image_spec='docker.io/jupyter/tensorflow-notebook:latest',
             singleuser_supplemental_gids=[100])
    ),
    (
        "Jupyter Project - R Notebook",
        'r-notebook',
        'kubespawner.KubeSpawner',
        dict(singleuser_image_spec='docker.io/jupyter/r-notebook:latest',
             singleuser_supplemental_gids=[100])
    )
]
```

The special setting is ``singleuser_supplemental_gids``, with it needing to be set to include the UNIX group ID of ``100``.

If you want to set this globally for all images in place of defining it for each image, or you were not providing a choice of image, you could instead set:

```
c.KubeSpawner.singleuser_supplemental_gids = [100]
```

Because of the size of these images, you may need to set a higher value for the spawner ``start_timeout`` setting to ensure starting a notebook instance from the image doesn't fail the first time a new node in the cluster is used for that image. Alternatively, you could have a cluster administrator pre-pull images to each node in the cluster.

Enabling the JupyterLab Interface
---------------------------------

If you have enabled the addition of the JupyterLab extension during the building of the Jupyter notebook images, or are using the official Jupyter project images, which already come bundled with the JupyterLab extension, you can enable it by setting the ``JUPYTER_ENABLE_LAB`` environment variable.

```
c.KubeSpawner.environment = dict(JUPYTER_ENABLE_LAB='true')
```

If using ``ProfilesSpawner`` to provide a list of multiple images and only want the JupyterLab interface enabled for certain images, add an ``environment `` setting to the dictionary of settings for just that image.

```
c.ProfilesSpawner.profiles = [
    (
        "Jupyter Project - Minimal Notebook",
        'minimal-notebook',
        'kubespawner.KubeSpawner',
        dict(singleuser_image_spec='docker.io/jupyter/minimal-notebook:latest',
             singleuser_supplemental_gids=[100],
             environment=dict(JUPYTER_ENABLE_LAB='true'))
    )
]
```

Controlling who can Access JupyterHub
-------------------------------------

When the templates are used to deploy JupyterHub, anyone will be able to access it and create a notebook instance. To provide access to only selected users, you will need to define an authenticator as part of the JupyterHub configuration. For example, if using GitHub as an OAuth provider, you would use:

```
from oauthenticator.github import GitHubOAuthenticator
c.JupyterHub.authenticator_class = GitHubOAuthenticator

c.GitHubOAuthenticator.oauth_callback_url = 'https://<your-jupyterhub-hostname>/hub/oauth_callback'
c.GitHubOAuthenticator.client_id = 'your-client-key-from-github'
c.GitHubOAuthenticator.client_secret = 'your-client-secret-from-github'

c.Authenticator.admin_users = {'your-github-username'}
c.Authenticator.whitelist = {'user1', 'user2', 'user3', 'user4'}
```

The ``oauthenticator`` package is installed by default and includes a number of commonly used authenticators. If you need to use a third party authenticator which requires additional Python packages to be installed, you will need to use the JupyterHub image as an S2I builder, where the source it is applied to includes a ``requirements.txt`` file including the list of additional Python packages to install. This will create a custom JupyterHub image which you can then deploy by overriding the ``JUPYTERHUB_IMAGE`` template parameter.

Allocating Persistent Storage to Users
--------------------------------------

When a notebook instance is created and a user creates their own notebooks if the instance is stopped they will loose any work they have done.

To avoid this, you can configure JupyterHub to make a persistent volume claim and mount storage into the containers when a notebook instance is run.

For the S2I enabled notebook images built previously, where the working directory when the notebook is run is ``/opt/app-root/src``, you can add the following to the JupyterHub configuration.

```
c.KubeSpawner.user_storage_pvc_ensure = True

c.KubeSpawner.pvc_name_template = '%s-nb-{username}' % c.KubeSpawner.hub_connect_ip
c.KubeSpawner.user_storage_capacity = '1Gi'

c.KubeSpawner.volumes = [
    {
        'name': 'data',
        'persistentVolumeClaim': {
            'claimName': c.KubeSpawner.pvc_name_template
        }
    }
]

c.KubeSpawner.volume_mounts = [
    {
        'name': 'data',
        'mountPath': '/opt/app-root/src'
    }
]
```

If you are presenting to users a list of images they can choose, if necessary you can add the spawner settings on selected images, and use a different mount path for the persistent volume if necessary.

Note that you should only use persistent storage when you are also using an authenticator and you know you have enough persistent volumes available to satisfy the needs of all potential users. This is because once a persistent volume is claimed and associated with a user, it is retained, even if the users notebook instance was shut down. If you want to reclaim persistent volumes, you will need to delete them manually using ``oc delete pvc``.

Also be aware that when you mount a persistent volume into a container, it will hide anything that was in the directory it is mounted on. If the working directory for the notebook in the image was pre-populated with files from an S2I build, these will be hidden if you use the same directory. When ``/opt/app-root/src`` is used as the mount point, only notebooks and other files create will be preserved. If you install additional Python packages, these will be lost when the notebook is shutdown, and you will need to reinstall them.

If you want to be able to pre-populate the persistent volume with notebooks and other files from the S2I built image, you can use the following configuration. This will also preserve additional Python packages which you might install.

```
c.KubeSpawner.user_storage_pvc_ensure = True

c.KubeSpawner.pvc_name_template = '%s-nb-{username}' % c.KubeSpawner.hub_connect_ip
c.KubeSpawner.user_storage_capacity = '2Gi'

c.KubeSpawner.volumes = [
    {
        'name': 'data',
        'persistentVolumeClaim': {
            'claimName': c.KubeSpawner.pvc_name_template
        }
    }
]

c.KubeSpawner.volume_mounts = [
    {
        'name': 'data',
        'mountPath': '/opt/app-root',
        'subPath': 'app-root'
    }
]

c.KubeSpawner.singleuser_init_containers = [
    {
        'name': 'setup-volume',
        'image': 'minimal-notebook:3.5',
        'command': [
            'setup-volume.sh',
            '/opt/app-root',
            '/mnt/app-root'
        ],
        'resources': {
            'limits': {
                'memory': '256Mi'
            }
        },
        'volumeMounts': [
            {
                'name': 'data',
                'mountPath': '/mnt'
            }
        ]
    }
]
```

Because the Python virtual environment and install packages are kept in the persistent volume in this case, you will need to ensure that you have adequate space in the persistent volume and may need to increase the requested storage capacity.

Culling Idle Notebook Instances
-------------------------------

When a notebook instance is created for a user, they will keep running until the user stops it, or OpenShift decides for some reason to stop them. In the latter, if the user was still using it, they would need to start it up again as notebook images will not be automatically restarted.

If you have many more users using the JupyterHub instance than you have memory and CPU resources, but you know not all users will use it at the same time, that is okay, so long as you shut down notebook instances when they have been idle, to free up resources.

To add culling of idle notebook instances, add to the JupyterHub configuration:

```
c.JupyterHub.services = [
    {
        'name': 'cull-idle',
        'admin': True,
        'command': ['cull-idle-servers', '--timeout=300'],
    }
]
```

The ``cull-idle-servers`` program is provided with the JupyterHub image. Adjust the value for the timeout argument as necessary.
