#!/bin/bash

# SPDX-FileCopyrightText: 2022 - 2023 Orthanc Team SRL <info@orthanc.team>
#
# SPDX-License-Identifier: CC0-1.0

# set -o xtrace
set -o errexit

enableHttps="${ENABLE_HTTPS:-false}"

ls -al /etc/nginx/disabled-conf/

if [[ $enableHttps == "true" ]]; then
  echo "ENABLE_HTTPS is true -> will listen on port 443 and read certificate from /etc/nginx/tls/crt.pem and private key from /etc/nginx/tls/key.pem"
  cp -f /etc/nginx/disabled-conf/ohif-nginx-https.conf /etc/nginx/conf.d/default.conf
else
  echo "ENABLE_HTTPS is false or not set -> will listen on port 80"
  cp -f /etc/nginx/disabled-conf/ohif-nginx-http.conf /etc/nginx/conf.d/default.conf
fi

# call the default nginx entrypoint
/docker-entrypoint.sh "$@"
