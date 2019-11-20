#!/usr/bin/env bash

set -x

cd req

for req in *.in; do
    pip-compile -Uv $req
done

pip-compile -Uv *.in -o combined.txt
pip-sync combined.txt
