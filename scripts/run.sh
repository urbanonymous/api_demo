#! /usr/bin/env sh

# Exit in case of error
set -e


docker run --name api-demo -d -p 8080:80 api-demo