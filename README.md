JupyterHub for OpenShift
========================

This repository contains software to make it easier to host Jupyter Notebooks on OpenShift using JupyterHub.

OpenShift, being a Kubernetes distribution, you can use the  [JupyterHub deployment method for Kubernetes](http://zero-to-jupyterhub.readthedocs.io/) created by the Jupyter project team. That deployment method relies on using Helm templates to manage deployment. The use of Helm, and that Kubernetes is a platform for IT operations, means it isn't as easy to deploy by end users as it could be. This repository aims to provide a much easier way of deploying JupyterHub to OpenShift which makes better use of OpenShift specific features, including OpenShift templates, and Source-to-Image (S2I) builders. The result is a method for deploying JupyterHub to OpenShift which doesn't require any special admin privileges to the underlying Kubernetes cluster, or OpenShift. As long as a user has the necessary quotas for memory, CPU and persistent storage, they can deploy JupyterHub themselves.

Preparing the Jupyter Images
----------------------------

The first step in deploying JupyterHub is to prepare the notebook images and the image for JupyterHub. Because the images provided by the Jupyter project will not run correctly in a multitenant Kubernetes cluster, such as OpenShift, with full role based access control enabled and where applications must run as a user ID specific to a project, it is necessary to create images which will work.

To create a minimal Jupyter notebook image, as well as images similar to the ``scipy`` and ``tensorflow`` notebooks provides by the Jupyter project team, run:

```
oc create -f https://raw.githubusercontent.com/jupyter-on-openshift/jupyter-notebooks/master/images.json
```

This will create a build configuration in your OpenShift project to build the images using the Python 3.5 S2I builder. You can watch the progress of the build for the minla Jupyter notebook image by running:

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
