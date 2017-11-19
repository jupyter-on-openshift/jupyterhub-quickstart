JupyterHub for OpenShift
========================

Ensure that default service account can use REST API to create resources.

```
oc create serviceaccount jupyterhub

oc policy add-role-to-user edit -z jupyterhub
```

Load image streams and templates for Jupyter Notebooks and JupyterHub.

```
oc create -f https://raw.githubusercontent.com/getwarped/jupyter-notebooks/master/openshift/images.json
oc create -f https://raw.githubusercontent.com/getwarped/jupyter-notebooks/master/openshift/templates.json

oc create -f https://raw.githubusercontent.com/getwarped/jupyter-spawner/master/templates/jupyterhub.json
```
