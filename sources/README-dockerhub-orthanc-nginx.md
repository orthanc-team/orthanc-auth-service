<!--
SPDX-FileCopyrightText: 2022 - 2023 Orthanc Team SRL <info@orthanc.team>

SPDX-License-Identifier: CC0-1.0
-->

# Orthanc-nginx

Web service to run in front of Orthanc to handle sharing of studies & admin interface.

| Environment variable (if `true`)                                                  | Description                                                                                                                 | route              | redirected to container                            |
|-----------------------------------------------------------------------------------|:----------------------------------------------------------------------------------------------------------------------------|:-------------------|:---------------------------------------------------|
| ENABLE_ORTHANC_FOR_ADMIN                                                          | Access to Orthanc for admin users                                                                                           | `/orthanc-admin/`  | `http://orthanc-for-admin:8042`                    |
| ENABLE_ORTHANC_FOR_SHARES                                                         | Access to Orthanc for `stone-viewer-publication` and `osimis-viewer-publication` shares                                     | `/shares/`         | `http://orthanc-for-shares:8042`                   |
| ENABLE_ORTHANC_FOR_ANON_SHARES                                                    | Access to an anonymized Orthanc for anonymized `osimis-viewer-publication` shares (not available for Stone)                 | `/anon-shares/`    | `http://orthanc-for-anon-shares:8042`              |
| ENABLE_ORTHANC_TOKEN_SERVICE                                                      | Access to the `token-service` that generates the shares.  Enable only if you have secured it with a list of allowed `USERS` | `/token-service/`  | `http://orthanc-token-service:8000`                |
| ENABLE_MEDDREAM                                                                   | Access to MedDream viewer for `meddream-viewer-publication` shares                                                          | `/meddream/`       | `http://meddream:8080`                             |
| Any of ENABLE_ORTHANC_FOR_SHARES, ENABLE_ORTHANC_FOR_ANON_SHARES, ENABLE_MEDDREAM | Access to `share-landing` service                                                                                           | `/welcome/`        | `http://orthanc-share-landing:8000/share-landing/` |
| ENABLE_ORTHANC_FOR_INGEST                                                         | Access to Orthanc for ingest (used by Gateways to push studies to Orthanc)                                                  | `/orthanc-ingest/` | `http://orthanc-for-ingest:8042`                   |
|                                                                                   |                                                                                                                             |                    |                                                    |
| ENABLE_HTTPS                                                                      | Enables HTTPS                                     | NA                 | NA                                                 |

If `ENABLE_HTTPS` is set to `true`, you must also provide a certificate file in `/etc/nginx/tls/crt.pem` and a private key in `/etc/nginx/tls/key.pem`.

Full documentation and demo setup will be available [here](https://github.com/orthanc-team/orthanc-share/tree/main).
