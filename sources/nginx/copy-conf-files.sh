#!/bin/bash

# SPDX-FileCopyrightText: 2022 - 2025 Orthanc Team SRL <info@orthanc.team>
#
# SPDX-License-Identifier: CC0-1.0

## configuration files management

# first (and only) arg should be a boolean:
# 'true' --> https
# 'false'--> http

set -o errexit

# get https
if [ "$1" == true ]; then
  https=true
else
  https=false
fi

enableOrthanc="${ENABLE_ORTHANC:-false}"
enableOrthancForApi="${ENABLE_ORTHANC_FOR_API:-false}"
enableOrthancForShares="${ENABLE_ORTHANC_FOR_SHARES:-false}"
enableKeycloak="${ENABLE_KEYCLOAK:-false}"
enableOrthancTokenService="${ENABLE_ORTHANC_TOKEN_SERVICE:-false}"
enableOhif="${ENABLE_OHIF:-false}"
enableMedDream="${ENABLE_MEDDREAM:-false}"
enableClientCert="${ENABLE_CLIENT_CERTIFICATE:-false}"

# manage proxy_read_timeout value
proxy_read_timeout="${PROXY_READ_TIMEOUT:-60}"
sed -i "s/proxy_read_timeout_placeholder/${proxy_read_timeout}s/g" /etc/nginx/includes/nginx-common.conf

# manage client cert verification
if [[ $enableClientCert == "true" && $https == "true" ]]; then
  echo "ENABLE_CLIENT_CERTIFICATE is true -> enable client certificate verification (root CA should be /etc/nginx/ssl/ca.crt!)"
  cp -f /etc/nginx/disabled-reverse-proxies/reverse-proxy.orthanc-cert.conf /etc/nginx/enabled-reverse-proxies/
fi

ls -al /etc/nginx/disabled-reverse-proxies/

if [[ $enableOrthanc == "true" ]]; then
  echo "ENABLE_ORTHANC is true -> enable /orthanc/ reverse proxy"
  cp -f /etc/nginx/disabled-reverse-proxies/reverse-proxy.orthanc.conf /etc/nginx/enabled-reverse-proxies/
fi

if [[ $enableOrthancForApi == "true" ]]; then
  echo "ENABLE_ORTHANC_FOR_API is true -> enable /orthanc-api/ reverse proxy"
  cp -f /etc/nginx/disabled-reverse-proxies/reverse-proxy.orthanc-api.conf /etc/nginx/enabled-reverse-proxies/
fi

if [[ $enableOrthancForShares == "true" ]]; then
  echo "ENABLE_ORTHANC_FOR_SHARES is true -> enable /shares/ reverse proxy"
  cp -f /etc/nginx/disabled-reverse-proxies/reverse-proxy.shares.conf /etc/nginx/enabled-reverse-proxies/
fi

if [[ $enableKeycloak == "true" ]]; then
  if [[ $https == "true" ]]; then
    echo "ENABLE_KEYCLOAK is true and ENABLE_HTTPS is true -> enable /keycloak/ reverse proxy in https version"
    cp -f /etc/nginx/disabled-reverse-proxies/reverse-proxy.keycloak-https.conf /etc/nginx/enabled-reverse-proxies/
  else
    echo "ENABLE_KEYCLOAK is true and ENABLE_HTTPS is false -> enable /keycloak/ reverse proxy in http version"
    cp -f /etc/nginx/disabled-reverse-proxies/reverse-proxy.keycloak-http.conf /etc/nginx/enabled-reverse-proxies/
  fi
fi

if [[ $enableOrthancTokenService == "true" ]]; then
  echo "ENABLE_ORTHANC_TOKEN_SERVICE is true -> enable /token-service/ reverse proxy"
  cp -f /etc/nginx/disabled-reverse-proxies/reverse-proxy.token-service.conf /etc/nginx/enabled-reverse-proxies/
fi

if [[ $enableMedDream == "true" ]]; then
  echo "ENABLE_MEDDREAM is true -> enable /meddream/ reverse proxy"
  cp -f /etc/nginx/disabled-reverse-proxies/reverse-proxy.meddream.conf /etc/nginx/enabled-reverse-proxies/
fi

if [[ $enableOhif == "true" ]]; then
  echo "ENABLE_OHIF is true -> enable /ohif/ reverse proxy"
  cp -f /etc/nginx/disabled-reverse-proxies/reverse-proxy.ohif.conf /etc/nginx/enabled-reverse-proxies/
fi
