#!/bin/bash

set -x

SERVICE=`echo $HOSTNAME | sed -e 's/^\(.*\)-[^-]*-[^-]*$/\1/'`
NAME=$SERVICE-$1

oc delete all --selector app=$NAME
