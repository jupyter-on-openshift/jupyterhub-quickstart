#!/bin/bash

set -x

NAME=$1

oc get svc/$NAME
