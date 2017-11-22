JupyterHub for OpenShift
========================

Ensure that default service account can use REST API to create resources.

```
oc create serviceaccount jupyterhub

oc policy add-role-to-user edit -z jupyterhub
```

Load build configuration, image streams and templates for Jupyter Notebooks
and JupyterHub.

```
oc apply -f https://raw.githubusercontent.com/getwarped/jupyter-spawner/master/resources/notebook.json
oc apply -f https://raw.githubusercontent.com/getwarped/jupyter-spawner/master/resources/jupyterhub.json
```

This will automatically trigger a build of a minimal Jupyter Notebook image
using Python 3.5.
