#!/bin/bash
# SPDX-FileCopyrightText: 2022 - 2026 Orthanc Team SRL <info@orthanc.team>
#
# SPDX-License-Identifier: CC0-1.0


# let's begin 2 tasks:
# the first task waits the Keycloak readyness to generate and print the Keycloak client secret
# the second task is the default entry point of Keycloak
# the first task will be started in background (thanks to the '&'), so the second task will start at the same time
cd /opt/keycloak/bin/
./regenerate-client-secret.sh &
./kc.sh start --optimized --import-realm --http-enabled true --proxy-headers xforwarded

