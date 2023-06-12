<!--
SPDX-FileCopyrightText: 2022 - 2023 Orthanc Team SRL <info@orthanc.team>

SPDX-License-Identifier: CC0-1.0
-->

# Orthanc-nginx

Web service to run in front of Orthanc to handle sharing of studies & admin interface.

| Environment variable (if `true`) | Default value | Description                                                                                                                     | route             | redirected to container             |
|----------------------------------|:--------------|:--------------------------------------------------------------------------------------------------------------------------------|:------------------|:------------------------------------|
| ENABLE_ORTHANC                   | true          | Access to the main Orthanc                                                                                                      | `/orthanc/` or `/`| `http://orthanc:8042`               |
| ENABLE_KEYCLOAK                  | false         | Access to Keycloak User Interface                                                                                               | `/keycloak/`      | `http://keycloak:8080`              |
| ENABLE_ORTHANC_TOKEN_SERVICE     | false         | Access to the `auth-service` that generates the shares.  Enable it only if you have secured it with a list of allowed `USERS`   | `/auth-service/`  | `http://orthanc-auth-service:8000` |
| ENABLE_MEDDREAM                  | false         | Access to MedDream viewer for `meddream-viewer-publication` shares                                                              | `/meddream/`      | `http://meddream:8080`              |
| ENABLE_ORTHANC_FOR_API           | false         | Access to Orthanc for api (e.g. for DicomWeb clients or scripts)                                                                | `/orthanc-api/`   | `http://orthanc-for-api:8042`       |
| ENABLE_ORTHANC_FOR_SHARES        | false         | Access to Orthanc for shares (publication links).  This is required only if you are not using keycloak and are enabling shares. | `/shares/`        | `http://orthanc-for-shares:8042`    |
|                                  |               |                                                                                                                                 |                   |                                     |
| ENABLE_HTTPS                     | false         | Enables HTTPS                                                                                                                   | NA                | NA                                  |

If `ENABLE_HTTPS` is set to `true`, you must also provide a certificate file in `/etc/nginx/tls/crt.pem` and a private key in `/etc/nginx/tls/key.pem`.

3 demo setups are available [here](https://github.com/orthanc-team/orthanc-auth-service/tree/main/minimal-setup).
