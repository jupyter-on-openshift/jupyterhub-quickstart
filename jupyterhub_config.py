c.JupyterHub.port = 8080
c.JupyterHub.hub_port = 8081
c.JupyterHub.proxy_api_port = 8082
c.JupyterHub.spawner_class = 'openshiftspawner.OpenShiftSpawner'
c.JupyterHub.authenticator_class = 'dummyauthenticator.DummyAuthenticator'
c.Spawner.http_timeout = 60
