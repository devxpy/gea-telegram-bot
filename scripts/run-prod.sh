#!/usr/bin/env bash

set -x

./manage.py collectstatic --no-input
./manage.py migrate
./caddy -conf scripts/Caddyfile &
./manage.py runtelebot &
gunicorn gea_bot.wsgi --bind unix:$HOME/gunicorn.sock
