#!/bin/bash
set -o xtrace
set -o errexit

pushd ../sources
docker build -t orthanc-team/orthanc-share .

popd

docker-compose --project-directory ..  up --build