#!/bin/bash
# set -o xtrace
set -o errexit

enableOrthancForAdmin="${ENABLE_ORTHANC_FOR_ADMIN:-false}"
enableOrthancForShares="${ENABLE_ORTHANC_FOR_SHARES:-false}"
enableOrthancForAnonShares="${ENABLE_ORTHANC_FOR_ANON_SHARES:-false}"
enableOrthancTokenService="${ENABLE_ORTHANC_TOKEN_SERVICE:-false}"
enableMedDream="${ENABLE_MEDDREAM:-false}"

ls -al /etc/nginx/disabled-reverse-proxies/

if [[ $enableOrthancForAdmin == "true" ]]; then
  echo "ENABLE_ORTHANC_FOR_ADMIN is true -> enable /orthanc-admin/ reverse proxy"
  cp -f /etc/nginx/disabled-reverse-proxies/reverse-proxy.orthanc-admin.conf /etc/nginx/enabled-reverse-proxies/
fi

if [[ $enableOrthancForShares == "true" ]]; then
  echo "ENABLE_ORTHANC_FOR_SHARES is true -> enable /shares/ reverse proxy"
  cp -f /etc/nginx/disabled-reverse-proxies/reverse-proxy.shares.conf /etc/nginx/enabled-reverse-proxies/
fi

if [[ $enableOrthancForAnonShares == "true" ]]; then
  echo "ENABLE_ORTHANC_FOR_ANON_SHARES is true -> enable /anon-shares/ reverse proxy"
  cp -f /etc/nginx/disabled-reverse-proxies/reverse-proxy.anon-shares.conf /etc/nginx/enabled-reverse-proxies/
fi

if [[ $enableOrthancTokenService == "true" ]]; then
  echo "ENABLE_ORTHANC_TOKEN_SERVICE is true -> enable /token-service/ reverse proxy"
  cp -f /etc/nginx/disabled-reverse-proxies/reverse-proxy.token-service.conf /etc/nginx/enabled-reverse-proxies/
fi

if [[ $enableMedDream == "true" ]]; then
  echo "ENABLE_MEDDREAM is true -> enable /meddream/ reverse proxy"
  cp -f /etc/nginx/disabled-reverse-proxies/reverse-proxy.meddream.conf /etc/nginx/enabled-reverse-proxies/
fi

if [[ $enableOrthancForShares == "true" || $enableOrthancForAnonShares == "true" || $enableMedDream == "true" ]]; then
  echo "enabling share landing -> enable /welcome/ reverse proxy"
  cp -f /etc/nginx/disabled-reverse-proxies/reverse-proxy.welcome.conf /etc/nginx/enabled-reverse-proxies/
fi

# call the default nginx entrypoint
/docker-entrypoint.sh "$@"
