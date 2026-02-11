#!/bin/bash

# SPDX-FileCopyrightText: 2022 - 2026 Orthanc Team SRL <info@orthanc.team>
#
# SPDX-License-Identifier: CC0-1.0

# set -o xtrace
set -o errexit

# configuration files management (true for https)

./scripts-ot/copy-conf-files.sh true

# domain name management

if [ -z "${DOMAIN_NAME}" ]; then
  echo "Error: DOMAIN_NAME is not set or is empty."
  exit 1
fi
domainName="${DOMAIN_NAME}"

sed -i "s/domain-name-placeholder/${domainName}/g" /etc/nginx/user_conf.d/orthanc-nginx-certbot.conf

# run ngix-certbot original entrypoint
./scripts/start_nginx_certbot.sh