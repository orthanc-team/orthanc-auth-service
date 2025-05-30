<!--
SPDX-FileCopyrightText: 2022 - 2025 Orthanc Team SRL <info@orthanc.team>

SPDX-License-Identifier: CC0-1.0
-->

# Orthanc-nginx-cerbot

Same as [orthancteam/orthanc-nginx](https://hub.docker.com/r/orthancteam/orthanc-nginx) with certbot included to handle tls thanks to let'encrypt.

On top of [orthancteam/orthanc-nginx](https://hub.docker.com/r/orthancteam/orthanc-nginx) env var, these have to be defined:


| Environment variables      | Default value                              | Description                                                                                                     |
|----------------------------|:-------------------------------------------|:----------------------------------------------------------------------------------------------------------------|
| DOMAIN_NAME                | -                                          | FQDN redirecting to the public IP of the server running Nginx.                                                  |
| CERTBOT_EMAIL              | -                                          | Email adress provided to lets'encrypt, could be used to send warnings about certificates about to expire.       |
| CERTBOT_AUTHENTICATOR      | "webroot"                                  | The authenticator plugin to use when responding to challenges. Default value is for HTTP challenge. Ini file with the credentials of the DNS server should be provided according to the chosen authenticator. For more details, see the [base image doc](https://github.com/JonasAlfredsson/docker-nginx-certbot/blob/master/docs/certbot_authenticators.md).|
| STAGING                    | 0                                          | Set to 1 to use Let's Encrypt's staging servers                                                                 |

NB: `ENABLE_HTTPS` env var decribed in [orthancteam/orthanc-nginx](https://hub.docker.com/r/orthancteam/orthanc-nginx) is not applicable in this version of the orthanc-nginx.