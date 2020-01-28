#!/usr/bin/env bash

set -ex

rm -rf deps
pip install . --target deps
cd deps
tar -cjf ../gea_bot_deps.tar.bz2 .
