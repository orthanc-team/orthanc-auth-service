<!--
SPDX-FileCopyrightText: 2022 - 2026 Orthanc Team SRL <info@orthanc.team>

SPDX-License-Identifier: CC-BY-4.0
-->

# Purpose

This is a sample setup to demonstrate how to implement an inbox for users to drop files
and optionaly fill a form and apply custom processing on the uploaded data.
This setup uses Keycloak to authenticate users.

# Description

This demo contains:

- an `orthanc` container.
- an `orthanc-db` container to handle the orthanc postgreSQL database.
- an `orthanc-auth-service` container that generates and validates tokens + interfaces with Keycloak.
- an `orthanc-keycloak` container that handles users and roles.
- a `keycloak-db` container to handle the keycloak postgreSQL database.
- an `orthanc-nginx` container acting as a reverse proxy in front of the other containers.
- an `ohif-v3` container hosting the OHIF viewer

# Warning

**Disclaimer**: this sample is provided 'as is' without any guarantee.  Don't use it in production unless you perfectly understand every part of it.

Before you use it in production make sure to update all hardcoded passwords and secret keys (search for `change-me`).

# Starting the setup

This setup is very similar to the `keycloak` one, check the README of the other project for base information.  Only the inbox is documented here.

# demo

## As a an anonymous user

- Open a new private browser window or open another browser
- Open the Orthanc UI at [http://localhost/orthanc/ui/app/inbox.html](http://localhost/orthanc/ui/app/inbox.html)
- Fill the form and upload a file


## As an admin user

- Open the Orthanc UI at [http://localhost/orthanc/ui/app/](http://localhost/orthanc/ui/app/) (login/pwd: `admin`/`change-me`)
- Check that the file has been uploaded and anonymized
