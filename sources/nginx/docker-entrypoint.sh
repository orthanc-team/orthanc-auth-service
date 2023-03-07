#!/bin/bash

# SPDX-FileCopyrightText: 2022 - 2023 Orthanc Team SRL <info@orthanc.team>
#
# SPDX-License-Identifier: CC0-1.0

# set -o xtrace
set -o errexit

enableOrthanc="${ENABLE_ORTHANC:-true}"
enableKeycloak="${ENABLE_KEYCLOAK:-true}"
enableOrthancTokenService="${ENABLE_ORTHANC_TOKEN_SERVICE:-false}"
enableHttps="${ENABLE_HTTPS:-false}"
enableMedDream="${ENABLE_MEDDREAM:-false}"

ls -al /etc/nginx/disabled-conf/

if [[ $enableHttps == "true" ]]; then
  echo "ENABLE_HTTPS is true -> will listen on port 443 and read certificate from /etc/nginx/tls/crt.pem and private key from /etc/nginx/tls/key.pem"
  cp -f /etc/nginx/disabled-conf/orthanc-nginx-https.conf /etc/nginx/conf.d/default.conf
else
  echo "ENABLE_HTTPS is false or not set -> will listen on port 80"
  cp -f /etc/nginx/disabled-conf/orthanc-nginx-http.conf /etc/nginx/conf.d/default.conf
fi

ls -al /etc/nginx/disabled-reverse-proxies/

if [[ $enableOrthanc == "true" ]]; then
  echo "ENABLE_ORTHANC is true -> enable /orthanc/ reverse proxy"
  cp -f /etc/nginx/disabled-reverse-proxies/reverse-proxy.orthanc.conf /etc/nginx/enabled-reverse-proxies/
fi

if [[ $enableKeycloak == "true" ]]; then
  echo "ENABLE_KEYCLOAK is true -> enable /keycloak/ reverse proxy"
  cp -f /etc/nginx/disabled-reverse-proxies/reverse-proxy.keycloak.conf /etc/nginx/enabled-reverse-proxies/
fi

if [[ $enableOrthancTokenService == "true" ]]; then
  echo "ENABLE_ORTHANC_TOKEN_SERVICE is true -> enable /token-service/ reverse proxy"
  cp -f /etc/nginx/disabled-reverse-proxies/reverse-proxy.token-service.conf /etc/nginx/enabled-reverse-proxies/
fi

if [[ $enableMedDream == "true" ]]; then
  echo "ENABLE_MEDDREAM is true -> enable /meddream/ reverse proxy"
  cp -f /etc/nginx/disabled-reverse-proxies/reverse-proxy.meddream.conf /etc/nginx/enabled-reverse-proxies/
fi

# call the default nginx entrypoint
/docker-entrypoint.sh "$@"
