#!/bin/bash

set -x

set -eo pipefail

# Add scripts directory to program search path.

PATH=$PATH:/opt/app-root/scripts

# Read any custom environment variables.

. /opt/app-root/etc/jupyterhub_config.sh

# Start the JupyterHub instance.

exec jupyterhub -f /opt/app-root/etc/jupyterhub_config.py
