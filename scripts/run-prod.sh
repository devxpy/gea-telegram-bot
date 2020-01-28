#!/usr/bin/env bash

set -x

wget -qO deps.tar.bz2 $DEPS_TARBALL
tar -xjf deps.tar.bz2 .

export PYTHONPATH=$PWD:$PYTHONPATH
export PATH=$PWD/bin:$PATH

./manage.py collectstatic --no-input
./manage.py migrate

./caddy -conf scripts/Caddyfile &
./manage.py runtelebot &
gunicorn gea_bot.wsgi --bind unix:$WORKDIR/gunicorn.sock
