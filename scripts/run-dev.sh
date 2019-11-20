#!/usr/bin/env bash

set -ex

trap 'docker rm -f gea-bot-postgres' SIGINT SIGTERM EXIT
docker run \
  -d --name gea-bot-postgres \
  -e POSTGRES_PASSWORD=password -p 5432:5432 -v "$PWD"/db:/var/lib/postgresql/data postgres
sleep 1
./manage.py runserver "$@"
