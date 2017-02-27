#!/bin/bash

set -x

SERVICE=`echo $HOSTNAME | sed -e 's/^\(.*\)-[^-]*-[^-]*$/\1/'`
NAME=$SERVICE-$1

oc get svc/$NAME
