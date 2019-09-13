if [ -f /opt/app-root/src/.jupyter/jupyterhub_config.sh ]; then
    . /opt/app-root/src/.jupyter/jupyterhub_config.sh
fi

if [ -f /opt/app-root/configs/jupyterhub_config.sh ]; then
    . /opt/app-root/configs/jupyterhub_config.sh
fi
