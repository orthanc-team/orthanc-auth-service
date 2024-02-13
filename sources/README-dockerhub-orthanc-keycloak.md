<!--
SPDX-FileCopyrightText: 2022 - 2024 Orthanc Team SRL <info@orthanc.team>

SPDX-License-Identifier: CC0-1.0
-->

# Orthanc-keycloak

Override of Keycloak official image to have these elements ready to use:
- realm (`orthanc` and `master`)
- client (`orthanc`)
- 2 sample users (`orthanc` and `doctor`, passwords are identical to usernames)
- 2 sample roles (`admin` and `doctor`)
- Orthanc logo on the login page

The `master` realm has an `admin` user with the `admin` password.

3 demo setups are available [here](https://github.com/orthanc-team/orthanc-auth-service/tree/main/minimal-setup).

## Disclaimer
This image is provided as a sample. It shouldn't be use as is!
Among other things to do for a production-ready setup there are:
- change the passwords
- handle tls !
