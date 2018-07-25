#!/bin/bash

source /opt/app-root/etc/scl_enable

export PYTHONUNBUFFERED=1

exec python `dirname $0`/cull-idle-servers.py "$@"
