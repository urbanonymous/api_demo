#! /usr/bin/env sh

set -e
set -x

docker exec -it api-demo cd .. & pytest tests_e2e