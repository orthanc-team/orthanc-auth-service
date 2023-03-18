<!--
SPDX-FileCopyrightText: 2022 - 2023 Orthanc Team SRL <info@orthanc.team>

SPDX-License-Identifier: CC-BY-4.0
-->

# Purpose

This is a sample setup to demonstrate how to share publication links granting access to a single study.
This setup uses Keycloak to authenticate users.

# Description

This demo contains:

- an `orthanc` container.
- an `orthanc-db` container to handle the orthanc postgreSQL database.
- an `orthanc-auth-service` container that generates and validates tokens + interfaces with Keycloak.
- an `orthanc-keycloak` container that handles users and roles.
- a `keycloak-db` container to handle the keycloak postgreSQL database.
- an `orthanc-nginx` container acting as a reverse proxy in front of the other containers.

# Starting the setup

To start the setup, type: `docker compose up`

# demo

## As an admin user

- Open the Orthanc UI at [http://localhost/orthanc/ui/app/](http://localhost/orthanc/ui/app/) (login/pwd: `orthanc`/`orthanc`)
- upload a dicom file in Orthanc
- On the uploaded file, click on the `Share` button and then on `Share` in the dialog box and then on `Copy and close`
- Keep the link in your clipboard.  You may share this link with an external user.
- Go to `Profile` -> `Logout`

## As a guest user

- Open a new private browser window or open another browser
- paste the link in the address bar
- this will open the Stone Viewer on the specific study but the guest user won't have access to other resources in Orthanc.

## As a doctor user

- Open the Orthanc UI at [http://localhost/orthanc/ui/app/](http://localhost/orthanc/ui/app/) (login/pwd: `doctor`/`doctor`)
- The doctor user is a restricted user who can browse the whole set of studies but who can not upload/modify/delete them.
