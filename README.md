JupyterHub for OpenShift
========================

This repository contains software to make it easier to host Jupyter Notebooks on OpenShift using JupyterHub.

OpenShift, being a Kubernetes distribution, you can use the  [JupyterHub deployment method for Kubernetes](http://zero-to-jupyterhub.readthedocs.io/) created by the Jupyter project team. That deployment method relies on using Helm templates to manage deployment. The use of Helm, and that Kubernetes is a platform for IT operations, means it isn't as easy to deploy by end users as it could be. This repository aims to provide a much easier way of deploying JupyterHub to OpenShift which makes better use of OpenShift specific features, including OpenShift templates, and Source-to-Image (S2I) builders. The result is a method for deploying JupyterHub to OpenShift which doesn't require any special admin privileges to the underlying Kubernetes cluster, or OpenShift. As long as a user has the necessary quotas for memory, CPU and persistent storage, they can deploy JupyterHub themselves.

Preparing the Jupyter Images
----------------------------

The first step in deploying JupyterHub is to prepare the notebook images and the image for JupyterHub. Because there are a number of issues with running the images provided by the Jupyter project in a multitenant Kubernetes cluster, such as OpenShift, with full role based access control enabled and where applications must run as a user ID specific to a project, it is preferable to create images which are designed properly to work with OpenShift.

To create a minimal Jupyter notebook image, as well as images similar to the ``scipy-notebook`` and ``tensorflow-notebook`` images provide by the Jupyter project team, run:

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

Enabling Access to the REST API
-------------------------------

The ``KubeSpawner`` plugin for JupyterHub which is used when deploying to OpenShift requires access to the Kubernetes REST API. When using OpenShift, this access is not enabled by default for applications as it is with plain Kubernetes.

To grant JupyterHub access to the REST API, first create a new service account called ``jupyterhub``.

```
oc create serviceaccount jupyterhub
```

When JupyterHub is run using the templates, it will be run under the ``jupyterhub`` service account instead of the ``default`` service account for a project.

Next grant this service account the ability to access the REST API, including being able to create and delete Kubernetes resource objects. This is done by giving the service account the ``edit`` role within the project.

```
oc policy add-role-to-user edit -z jupyterhub
```

You can check that the role has been added correctly by running ``oc get rolebindings``. You should see an entry for the ``edit`` role of:

```
NAME  ROLE  USERS  GROUPS  SERVICE ACCOUNTS  SUBJECTS
edit  /edit                jupyterhub
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
oc delete all,configmap,pvc --selector app=jupyterhub
```

Deploying with a Custom Notebook Image
--------------------------------------

To deploy JupyterHub and have it build a custom notebook image for you, run:

```
oc new-app --template jupyterhub-quickstart \
  --param APPLICATION_NAME=jakevdp \
  --param GIT_REPOSITORY_URL=https://github.com/jakevdp/PythonDataScienceHandbook
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
oc delete all,configmap,pvc --selector app=jakevdp
```

Using the OpenShift Web Console
-------------------------------

JupyterHub can also be deployed from the web console by selecting _Browse Catalog_ from the _Add to Project_ menu, filtering on _jupyter_ and choosing the appropriate template.

Customising the JupyterHub Deployment
-------------------------------------

JupyterHub, and how notebook images are deployed, can be customised through a ``jupyterhub_config.py`` file. The JupyterHub image created from this repository has a default version of this file which sets a number of defaults required for running JupyterHub in OpenShift. You can provide your own customisations, including overriding any defaults, in a couple of ways.

The first is that when using the supplied templates to deploy JupyterHub, you can provide your own configuration through the ``JUPYTERHUB_CONFIG`` template parameter. This configuration will be read after the default configuration, with any settings being merged with the existing settings.

The second is to use the JupyterHub image built from this repository as an S2I builder, to incorporate your own ``jupyterhub_config.py`` file from a hosted Git repository, or local directory if using a binary input build. This will be merged with the default settings before any configuration supplied via ``JUPYTERHUB_CONFIG`` when using a template to deploy the JupyterHub image.

When using an S2I build, the repository can include any additional files to be incorporated into the JupyterHub image which may be needed for your customisations. This includes being able to supply a ``requirements.txt`` file for additional Python packages to be installed, as may be required by an authenticator to be used with JupyterHub.

To illustrate overriding the configuration when deploying JupyterHub using the quick start template, create a local file ``jupyterhub_config.py`` which contains:

```
c.KubeSpawner.start_timeout = 120
c.KubeSpawner.http_timeout = 60
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

When deploying JupyterHub using the templates, the ``NOTEBOOK_IMAGE`` template parameter is used to specify the name of the image which is to be deployed when starting an instance for a user. If you want to provide users a choice of image, the value passed for ``NOTEBOOK_IMAGE`` can be a comma separated list of image names. The list of images will be presented in a drop down menu when the user requests a notebook instance be started through the JupyterHub web interface.

When multiple choices are available, the user can still only have one notebook instance running at a time. If they want to switch which image they are using, they need to use the _Control Panel_ in the JupyterHub web interface to stop the existing notebook instance. They can then start a new instance with a different image.

The name of image should be the name of the image stream in the same project JupyterHub is deployed, including an image tag if not ``latest``, or can be the full image name identifying an image on a remote image registry.

If you want the name displayed for an image in the web interface when choosing the image, to be different to the image name, you will need to specify the set of images from the JupyterHub configuration.

```
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

This will override any images listed in the ``NOTEBOOK_IMAGE`` template parameter.

The first value in the tuple for an image is the display name. The second value is a unique key identifying the selection. The third value should always be ``kubespawner.KubeSpawner``. The final value is a dictionary with the settings to be applied to the spawner when deploying the image.

In this case, the ``singleuser_image_spec`` setting should be set to the name for the deployed image. This dictionary can be used to set other per image specific settings if required.

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

will not work out of the box with OpenShift. This is because they have not been designed properly to work with an assigned user ID. The images are also very large and the size exceeds what can be deployed to hosted OpenShift environments such as OpenShift Online.

Because of the problems with the official Jupyter Project notebook images, it is recommended, for Python at least, to use the similar notebook images built above. These images have the benefit of also being S2I enabled.

If you still want to run the official Jupyter Project notebook images, you can, but you will need to supply special configuration to the ``KubeSpanwer`` plugin for these images to have them work. For example:

```
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

Even though this allows the images to be run, you may still encounter issues, as the images do not dynamically provide ``passwd`` and ``group`` file entries in the case the container is run as an assigned user ID different to what the image defines. The lack of these entries can cause software to fail when it doesn't gracefully handle the lack of an entry.

Because of the size of these images, you may need to set a higher value for the spawner ``start_timeout`` setting to ensure starting a notebook instance from the image doesn't fail the first time a new node in the cluster is used for that image. Alternatively, you could have a cluster administrator pre-pull images to each node in the cluster.
