#! /usr/bin/env sh

# Exit in case of error
set -e

docker exec -it api-demo pytest app/api/tests