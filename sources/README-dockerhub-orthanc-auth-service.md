<!--
SPDX-FileCopyrightText: 2022 - 2023 Orthanc Team SRL <info@orthanc.team>

SPDX-License-Identifier: CC0-1.0
-->

# Orthanc-token-service

Web service to run next to Orthanc to handle sharing of studies by issuing [JWT](https://jwt.io/) that can then be passed
in authorization headers that will be checked by the [Authorization plugin](https://book.orthanc-server.com/plugins/authorization.html).

| Environment variables | Default value                          | Description                                                                                                                                                     |
|-----------------------|:---------------------------------------|:----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| ENABLE_KEYCLOAK       | false                                  | Connects the auth-service to keycloak to handle users                                                                                                           |
| KEYCLOAK_URI          | http://keycloak:8080/realms/orthanc/   | The URI of the realm to use.                                                                                                                                    |
| PERMISSIONS_FILE_PATH | /orthanc-auth-service/permissions.json | Path to a file containing the mapping between keycloak roles and permissions.                                                                                   |
|                       |                                        |                                                                                                                                                                 |
| PUBLIC_ORTHANC_ROOT   | -                                      | The public path to Orthanc when using links to access resources. e.g: `http://localhost/orthanc/`                                                               |
| PUBLIC_LANDING_ROOT   | -                                      | The landing page for links.  This page will check the token validity and redirect to e.g. a viewer.  e.g.: `http://localhost/orthanc/ui/app/token-landing.html` |
| USERS                 | -                                      | Define a list of user/pwd that can access this webservice.                                                                                                      |


Full documentation and demo setup will be available [here](https://github.com/orthanc-team/orthanc-share/tree/main).
