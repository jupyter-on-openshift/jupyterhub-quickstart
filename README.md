JupyterHub for OpenShift
========================

This repository contains software to make it easier to host Jupyter Notebooks on OpenShift using JupyterHub.

OpenShift, being a Kubernetes distribution, you can use the [JupyterHub deployment method for Kubernetes](http://zero-to-jupyterhub.readthedocs.io/) created by the Jupyter project team. That deployment method relies on using Helm templates to manage deployment. The use of Helm, and that Kubernetes is a platform for IT operations, means it isn't as easy to deploy by end users as it could be. This repository aims to provide a much easier way of deploying JupyterHub to OpenShift which makes better use of OpenShift specific features, including OpenShift templates, and Source-to-Image (S2I) builders. The result is a method for deploying JupyterHub to OpenShift which doesn't require any special admin privileges to the underlying Kubernetes cluster, or OpenShift. As long as a user has the necessary quotas for memory, CPU and persistent storage, they can deploy JupyterHub themselves.

Use a stable version of this repository
---------------------------------------

When using this repository, and the parallel ``jupyter-notebooks`` repository, unless you are participating in the development and testing of the images produced from these repositories, always use a tagged version. Do not use master or development branches as your builds or deployments could break across versions.

You should therefore always use any files for creating images or templates from the required tagged version. These will reference the appropriate version. If you have created your own resource definitions to build from the repository, ensure that the ref field of the Git settings for the build refers to the desired version.

Preparing the Jupyter Images
----------------------------

The first step in deploying JupyterHub is to prepare a notebook image and the image for JupyterHub.

You can use the official Jupyter project ``docker-stacks`` images, but some extra configuration is required to use those as they will not work out of the box with OpenShift. Details on how to use the Jupyter project images is described later.

To load an image stream definition for a minimal Jupyter notebook image designed to run in OpenShift, run:

```
oc create -f https://raw.githubusercontent.com/jupyter-on-openshift/jupyter-notebooks/master/image-streams/s2i-minimal-notebook.json
```

An image stream named ``s2i-minimal-notebook`` should be created in your project, with tags ``3.5`` and ``3.6``, corresponding to Python 3.5 and 3.6 variants of the notebook image. This image is based on CentOS.

For more detailed instructions on creating the minimal notebook image, including how to build it from source code or using a RHEL base image, as well as how to create custom notebook images, read:

* https://github.com/jupyter-on-openshift/jupyter-notebooks

To load the JupyterHub image, next run:

```
oc create -f https://raw.githubusercontent.com/jupyter-on-openshift/jupyterhub-quickstart/master/image-streams/jupyterhub.json
```

An image stream named ``jupyterhub`` should be created in your project, with a tag corresponding to whatever is the latest version. This image is also based on CentOS.

If you are using OpenShift Container Platform, and need to instead build a RHEL based version of the JupyterHub image, you can use the command:

```
oc create -f https://raw.githubusercontent.com/jupyter-on-openshift/jupyterhub-quickstart/master/build-configs/jupyterhub.json
```

Use one or the other method. Do not load the image stream and try and create a build config to create it, at the same time.

Loading the JupyterHub Templates
--------------------------------

To make it easier to deploy JupyterHub in OpenShift, templates are provided. To load the templates run:

```
oc create -f https://raw.githubusercontent.com/jupyter-on-openshift/jupyterhub-quickstart/master/templates/jupyterhub-builder.json
oc create -f https://raw.githubusercontent.com/jupyter-on-openshift/jupyterhub-quickstart/master/templates/jupyterhub-deployer.json
oc create -f https://raw.githubusercontent.com/jupyter-on-openshift/jupyterhub-quickstart/master/templates/jupyterhub-quickstart.json
```

This should result in the creation of the templates ``jupyterhub-builder``, ``jupyterhub-deployer`` and ``jupyterhub-quickstart``.

Creating the JupyterHub Deployment
----------------------------------

To deploy JupyterHub with the default configuration, which will provide you a deployment similar to ``tmpnb.org``, and using the ``s2i-minimal-notebook:3.6`` image, run:

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

Note that the first notebook instance deployed may be slow to start up as the notebook image may need to be pulled down from the image registry.

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
  --param GIT_REPOSITORY_URL=https://github.com/jakevdp/PythonDataScienceHandbook \
  --param BUILDER_IMAGE=s2i-minimal-notebook:3.5
```

The ``s2i-minimal-notebook:3.5`` builder image is used in this specific case instead of the default ``s2i-minimal-notebook:3.6`` build image, as the repository being used as input to the S2I build only supports Python 3.5.

The notebook image will be built in parallel to JupyterHub being deployed. You will need to wait until the build of the image has completed before you can visit JupyterHub the first time. You can monitor the build of the image using the command:

```
oc logs bc/jakevdp-nb --follow
```

To deploy JupyterHub using a custom notebook image you had already created, run:

```
oc new-app --template jupyterhub-deployer \
  --param APPLICATION_NAME=jakevdp \
  --param NOTEBOOK_IMAGE=jakevdp-nb:latest
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

When deploying JupyterHub using the templates, the ``NOTEBOOK_IMAGE`` template parameter is used to specify the name of the image which is to be deployed when starting an instance for a user. If you want to provide users a choice of images you will need to define what is called a profile list in the configuration. The list of images will be presented in a drop down menu when the user requests a notebook instance be started through the JupyterHub web interface.

```
c.KubeSpawner.profile_list = [
    {
        'display_name': 'Minimal Notebook (CentOS 7 / Python 3.5)',
        'kubespawner_override': {
            'image_spec': 's2i-minimal-notebook:3.5'
        }
    },
    {
        'display_name': 'Minimal Notebook (CentOS 7 / Python 3.6)',
        'default': True,
        'kubespawner_override': {
            'image_spec': 's2i-minimal-notebook:3.6'
        }
    }
]
```

This will override any image defined by the ``NOTEBOOK_IMAGE`` template parameter.

For further information on using the profile list configuration see the ``KubeSpawner`` documentation.

* https://jupyterhub-kubespawner.readthedocs.io/en/latest/spawner.html

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

If you still want to run the official Jupyter Project notebook images, you can, but you will need to supply additional configuration to the ``KubeSpawner`` plugin for these images to have them work. For example:

```
c.KubeSpawner.profile_list = [
    {
        'display_name': 'Jupyter Project - Minimal Notebook',
        'default': True,
        'kubespawner_override': {
            'image_spec': 'docker.io/jupyter/minimal-notebook:latest',
            'supplemental_gids': [100]
        }
    },
    {
        'display_name': 'Jupyter Project - Scipy Notebook',
        'kubespawner_override': {
            'image_spec': 'docker.io/jupyter/scipy-notebook:latest',
            'supplemental_gids': [100]
        }
    },
    {
        'display_name': 'Jupyter Project - Tensorflow Notebook',
        'kubespawner_override': {
            'image_spec': 'docker.io/jupyter/tensorflow-notebook:latest',
            'supplemental_gids': [100]
        },
    }
]
```

The special setting is ``supplemental_gids``, with it needing to be set to include the UNIX group ID of ``100``.

If you want to set this globally for all images in place of defining it for each image, or you were not providing a choice of image, you could instead set:

```
c.KubeSpawner.supplemental_gids = [100]
```

Because of the size of these images, you may need to set a higher value for the spawner ``start_timeout`` setting to ensure starting a notebook instance from the image doesn't fail the first time a new node in the cluster is used for that image. Alternatively, you could have a cluster administrator pre-pull images to each node in the cluster.

Enabling the JupyterLab Interface
---------------------------------

By default Jupyter Notebook images still use the classic web interface by default. If you want to enable the newer JupyterLab web interface set the ``JUPYTER_ENABLE_LAB`` environment variable.

```
c.KubeSpawner.environment = { 'JUPYTER_ENABLE_LAB': 'true' }
```

If using a profile list and only want the JupyterLab interface enabled for certain images, add an ``environment`` setting to the dictionary of settings for just that image.

```
c.KubeSpawner.profile_list = [
    {
        'display_name': 'Minimal Notebook (Classic)',
        'default': True,
        'kubespawner_override': {
            'image_spec': 's2i-minimal-notebook:3.6'
        }
    },
    {
        'display_name': 'Minimal Notebook (JupyterLab)',
        'kubespawner_override': {
            'image_spec': 's2i-minimal-notebook:3.6',
            'environment': { 'JUPYTER_ENABLE_LAB': 'true' }
        }
    }
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
        'mountPath': '/opt/app-root',
        'subPath': 'app-root'
    }
]

c.KubeSpawner.singleuser_init_containers = [
    {
        'name': 'setup-volume',
        'image': 's2i-minimal-notebook:3.6',
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

Because the Python virtual environment and installed packages are kept in the persistent volume in this case, you will need to ensure that you have adequate space in the persistent volume and may need to increase the requested storage capacity.

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
