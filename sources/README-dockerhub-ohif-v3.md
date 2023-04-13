<!--
SPDX-FileCopyrightText: 2022 - 2023 Orthanc Team SRL <info@orthanc.team>

SPDX-License-Identifier: CC0-1.0
-->

# ohif-v3

Web service to run next to Orthanc to host [OHIF v3 viewer](https://github.com/OHIF/Viewers/tree/v3-stable)

| Environment variable (if `true`) | Default value | Description                                                                                                                     | route             | redirected to container             |
|----------------------------------|:--------------|:--------------------------------------------------------------------------------------------------------------------------------|:------------------|:------------------------------------|
| ENABLE_HTTPS                     | false         | Enables HTTPS                                                                                                                   | NA                | NA                                  |

If `ENABLE_HTTPS` is set to `true`, you must also provide a certificate file in `/etc/nginx/tls/crt.pem` and a private key in `/etc/nginx/tls/key.pem`.

This container assumes that an Orthanc container is running in the same network and its hostname is `orthanc`

You may possibly override the [default OHIF configuration](https://github.com/orthanc-team/orthanc-auth-service/tree/main/sources/ohif/default-app-config.js) by providing a custom file in `/usr/share/nginx/html/app-config.js`

A demo setup is available [here](https://github.com/orthanc-team/orthanc-auth-service/tree/main/minimal-setup/keycloak).
