#!/bin/bash
set -o xtrace
set -o errexit

pushd ../sources
docker build -t orthancteam/orthanc-share -f Dockerfile.orthanc-share .
docker build -t orthancteam/orthanc-anonymizer  -f Dockerfile.orthanc-anonymizer .

popd

docker-compose --project-directory ..  up --build