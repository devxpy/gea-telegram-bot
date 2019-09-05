#!/usr/bin/env bash

set -x

docker run \
    -v $PWD:$PWD \
    -v $HOME/.cache/pip:/root/.cache/pip \
    -w $PWD \
    python:3.7 \
    pip install -r req/main.txt --target dist

cd dist
tar -cjf ../deps.tar.bz2 .
cd ..
rm -r dist
