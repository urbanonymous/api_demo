#! /usr/bin/env sh

set -e
set -x

docker stop api-demo
docker rm api-demo