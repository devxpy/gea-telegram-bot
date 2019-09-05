#!/usr/bin/env bash

set -x

cd req
pip install -U pip-tools

for req in *.in; do
    pip-compile -Uv $req
done

pip-compile -Uv *.in -o combined.txt
pip-sync combined.txt
