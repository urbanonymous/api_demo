#! /usr/bin/env sh

# Exit in case of error
set -e

docker stop api-demo
docker rm api-demo