#!/bin/bash

set -x

exec jupyterhub -f jupyterhub_config.py
