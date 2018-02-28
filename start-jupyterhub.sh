#!/bin/bash

set -eo pipefail

# Add scripts directory to program search path.

PATH=$PATH:/opt/app-root/scripts

# Start the JupyterHub instance.

exec jupyterhub -f /opt/app-root/etc/jupyterhub_config.py
