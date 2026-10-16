<!--
SPDX-FileCopyrightText: 2022 - 2026 Orthanc Team SRL <info@orthanc.team>

SPDX-License-Identifier: CC0-1.0
-->

# Orthanc-keycloak

Override of Keycloak official image to have these elements ready to use:
- realm (`orthanc` and `master`)
- client (`orthanc`)
- 2 sample users (`orthanc` and `doctor`, passwords are `change-me` and must be changed !!!!)
- 2 sample roles (`admin-role`, `doctor-role` and `interhosp-role`)
- Orthanc logo on the login page

The `master` realm has an `admin` user with a password that must be defined in a `KC_BOOTSTRAP_ADMIN_PASSWORD` secret.

3 demo setups are available [here](https://github.com/orthanc-team/orthanc-auth-service/tree/main/minimal-setup).

## Disclaimer
This image is provided as a sample. It shouldn't be use as is!
Among other things to do for a production-ready setup there are:
- change the passwords
- handle tls !


|    Environment variables    |                Default value                |           Description            |
| --------------------------- | :------------------------------------------ | :------------------------------- |
| KC_DB_URL                   | jdbc:postgresql://keycloak-db:5432/postgres | Url to the postgres DB           |
| KC_DB_USERNAME              | postgres                                    | postgres username                |
| KC_DB_PASSWORD              | postgres                                    | postgres password                |
| KC_BOOTSTRAP_ADMIN_USERNAME | admin                                       | Username for keycloak super user |


