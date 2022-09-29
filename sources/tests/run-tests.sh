#!/bin/bash
set -o xtrace
set -o errexit

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

pushd $SCRIPT_DIR/..

python -m unittest $SCRIPT_DIR/test_tokens.py

popd