#!/bin/bash

# SPDX-FileCopyrightText: 2022 - 2023 Orthanc Team SRL <info@orthanc.team>
#
# SPDX-License-Identifier: CC0-1.0

set -o xtrace
set -o errexit

pushd ../sources
docker build -t orthancteam/orthanc-nginx -f nginx/Dockerfile.orthanc-nginx .
docker build -t orthancteam/orthanc-token-service -f Dockerfile.orthanc-token-service .
docker build -t orthancteam/meddream-viewer  -f meddream/viewer/Dockerfile.meddream-viewer ./meddream/viewer
docker build -t orthancteam/meddream-token-service  -f meddream/token-service/Dockerfile.meddream-token-service ./meddream/token-service

popd

COMPOSE_FILE=docker-compose.yml:docker-compose.meddream.yml docker-compose --project-directory ..  up --build