#! /usr/bin/env sh

set -e
set -x


docker run --name api-demo -d -p 8080:80 api-demo