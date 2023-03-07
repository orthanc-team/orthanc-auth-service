#!/bin/bash

# SPDX-FileCopyrightText: 2022 - 2023 Orthanc Team SRL <info@orthanc.team>
#
# SPDX-License-Identifier: CC0-1.0

set -o xtrace
set -o errexit

pushd ../sources
docker build -t orthancteam/orthanc-nginx -f nginx/Dockerfile.orthanc-nginx .
docker build -t orthancteam/orthanc-auth-service -f Dockerfile.orthanc-auth-service .

popd

COMPOSE_FILE=docker-compose.yml docker-compose --project-directory ..  up --build