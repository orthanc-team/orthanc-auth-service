#!/bin/bash

# SPDX-FileCopyrightText: 2022 - 2024 Orthanc Team SRL <info@orthanc.team>
#
# SPDX-License-Identifier: CC0-1.0

# set -o xtrace
set -o errexit

enableOrthanc="${ENABLE_ORTHANC:-false}"
enableOrthancForApi="${ENABLE_ORTHANC_FOR_API:-false}"
enableOrthancForShares="${ENABLE_ORTHANC_FOR_SHARES:-false}"
enableKeycloak="${ENABLE_KEYCLOAK:-false}"
enableOrthancTokenService="${ENABLE_ORTHANC_TOKEN_SERVICE:-false}"
enableOhif="${ENABLE_OHIF:-false}"
enableMedDream="${ENABLE_MEDDREAM:-false}"

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
  echo "ENABLE_KEYCLOAK is true -> enable /keycloak/ reverse proxy"
  cp -f /etc/nginx/disabled-reverse-proxies/reverse-proxy.keycloak-https.conf /etc/nginx/enabled-reverse-proxies/
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