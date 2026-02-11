<!--
SPDX-FileCopyrightText: 2022 - 2026 Orthanc Team SRL <info@orthanc.team>

SPDX-License-Identifier: CC0-1.0
-->

# ohif-v3

Web service to run next to Orthanc to host [OHIF v3 viewer](https://github.com/OHIF/Viewers/tree/v3-stable).
It assumes it is running behind a reverse proxy at the `/ohif/` route and that Orthanc is available at the `/orthanc/` route.

You may possibly override the [default OHIF configuration](https://github.com/orthanc-team/orthanc-auth-service/tree/main/sources/ohif/default-app-config.js) by providing a custom file in `/usr/share/nginx/html/app-config.js`

A demo setup is available [here](https://github.com/orthanc-team/orthanc-auth-service/tree/main/minimal-setup/keycloak).
