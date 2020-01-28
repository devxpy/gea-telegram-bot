#!/usr/bin/env bash

set -ex

docker run -it \
    -v $PWD:$PWD \
    -w $PWD \
    python:3.8 \
    "$@"
