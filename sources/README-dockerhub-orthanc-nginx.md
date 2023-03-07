<!--
SPDX-FileCopyrightText: 2022 - 2023 Orthanc Team SRL <info@orthanc.team>

SPDX-License-Identifier: CC0-1.0
-->

# Orthanc-nginx

Web service to run in front of Orthanc to handle sharing of studies & admin interface.

| Environment variable (if `true`)                                                   | Default value | Description                                                                                                                 | route              | redirected to container             |
|------------------------------------------------------------------------------------|:--------------|:----------------------------------------------------------------------------------------------------------------------------|:-------------------|:------------------------------------|
| ENABLE_ORTHANC                                                                     | true          | Access to Orthanc for admin users                                                                                           | `/orthanc-admin/`  | `http://orthanc:8042`               |
| ENABLE_ORTHANC_TOKEN_SERVICE                                                       | false         | Access to the `token-service` that generates the shares.  Enable only if you have secured it with a list of allowed `USERS` | `/token-service/`  | `http://orthanc-token-service:8000` |
| ENABLE_MEDDREAM                                                                    | false         | Access to MedDream viewer for `meddream-viewer-publication` shares                                                          | `/meddream/`       | `http://meddream:8080`              |
|                                                                                    |               |                                                                                                                             |                    |                                     |
| ENABLE_HTTPS                                                                       |               | Enables HTTPS                                                                                                               | NA                 | NA                                  |

If `ENABLE_HTTPS` is set to `true`, you must also provide a certificate file in `/etc/nginx/tls/crt.pem` and a private key in `/etc/nginx/tls/key.pem`.

Full documentation and demo setup will be available [here](https://github.com/orthanc-team/orthanc-share/tree/main).
