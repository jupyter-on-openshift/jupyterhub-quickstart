#!/bin/bash

set -x

NAME=$1

oc delete all --selector app=$NAME
