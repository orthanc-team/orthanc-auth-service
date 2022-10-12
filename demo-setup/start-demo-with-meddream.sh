#!/bin/bash
set -o xtrace
set -o errexit

pushd ../sources
docker build -t orthancteam/orthanc-nginx -f nginx/Dockerfile.orthanc-nginx .
docker build -t orthancteam/orthanc-token-service -f Dockerfile.orthanc-token-service .
docker build -t orthancteam/orthanc-anonymizer  -f Dockerfile.orthanc-anonymizer .
docker build -t orthancteam/orthanc-share-landing  -f Dockerfile.orthanc-share-landing .
docker build -t orthancteam/meddream-viewer  -f meddream/viewer/Dockerfile.meddream-viewer ./meddream/viewer
docker build -t orthancteam/meddream-token-service  -f meddream/token-service/Dockerfile.meddream-token-service ./meddream/token-service

popd

COMPOSE_FILE=docker-compose.yml:docker-compose.meddream.yml docker-compose --project-directory ..  up --build