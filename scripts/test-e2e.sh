#! /usr/bin/env sh

set -e
set -x

docker exec -it api-demo bash -c 'cd .. ; pytest tests_e2e/'
