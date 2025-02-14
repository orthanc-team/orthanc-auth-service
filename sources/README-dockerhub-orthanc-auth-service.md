<!--
SPDX-FileCopyrightText: 2022 - 2025 Orthanc Team SRL <info@orthanc.team>

SPDX-License-Identifier: CC0-1.0
-->

# Orthanc-auth-service

Web service to run next to Orthanc to handle sharing of studies by issuing [JWT](https://jwt.io/) that can then be passed
in authorization headers that will be checked by the [Authorization plugin](https://book.orthanc-server.com/plugins/authorization.html).

| Environment variables      | Default value                              | Description                                                                                                                                                         |
|----------------------------|:-------------------------------------------|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| ENABLE_KEYCLOAK            | false                                      | Connects the auth-service to keycloak to handle users                                                                                                               |
| KEYCLOAK_URI               | http://keycloak:8080/realms/orthanc/       | The URI of the realm to use.                                                                                                                                        |
| PERMISSIONS_FILE_PATH      | /orthanc-auth-service/permissions.json     | Path to a file containing the mapping between keycloak roles and permissions.                                                                                       |
|                            |                                            |                                                                                                                                                                     |
| ENABLE_KEYCLOAK_API_KEYS   | false                                      | Enables the API keys support in Keycloak                                                                                                                            | 
| KEYCLOAK_ADMIN_URI         | http://keycloak:8080/admin/realms/orthanc/ | The URI of admin API of the realm to use.                                                                                                                           |
| KEYCLOAK_CLIENT_SECRET     | -                                          | `admin-cli` client secret used to authenticate to the Keycloak admin API                                                                                            |
|                            |                                            |                                                                                                                                                                     |
| PUBLIC_ORTHANC_ROOT        | -                                          | The public root URL to Orthanc when using links to access resources. e.g: `http://localhost/orthanc/`                                                               |
| PUBLIC_LANDING_ROOT        | -                                          | The landing page URL for links.  This page will check the token validity and redirect to e.g. a viewer.  e.g.: `http://localhost/orthanc/ui/app/token-landing.html` |
| PUBLIC_OHIF_ROOT           | -                                          | The public root URL to OHIF when using links to access resources. e.g: `https://ohif.my.site/`                                                                      |
| USERS                      | -                                          | Define a list of user/pwd that can access this webservice.                                                                                                          |
|                            |                                            |                                                                                                                                                                     |
| MEDDREAM_TOKEN_SERVICE_URL | -                                          | The URL to the MedDream token service. e.g `http://meddream-token-service:8088/v3/generate`                                                                         |
| PUBLIC_MEDDREAM_ROOT       | -                                          | The public root URL to access the MedDream viewer. e.g `http://localhost/meddream/`                                                                                 |

3 demo setups are available [here](https://github.com/orthanc-team/orthanc-auth-service/tree/main/minimal-setup).
