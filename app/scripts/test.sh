#! /usr/bin/env bash

# Exit in case of error
set -e

# Run this from the root of the project

bash ./scripts/test.sh "$@"

cd ../