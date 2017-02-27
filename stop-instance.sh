#!/bin/bash

set -x

SERVICE=$1
NAME=$2

oc delete all --selector app=$NAME
