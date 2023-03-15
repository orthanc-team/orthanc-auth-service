<!--
SPDX-FileCopyrightText: 2022 - 2023 Orthanc Team SRL <info@orthanc.team>

SPDX-License-Identifier: CC-BY-4.0
-->

# Purpose

This is a sample setup to demonstrate how to run Orthanc-Explorer-2 together with the `orthanc-auth-service`
web-service to provide tokens to authenticate users or grant access to specific resources e.g. by providing public links to specific studies. The authentication and the roles of the users are handled by Keycloak.

**Disclaimer**: this sample is provided 'as is' without any guarantee.  Don't use it in production unless you perfectly understand every part of it.

# Description

This demo contains:

- a nginx container that provides a web server on port 80.  
- It exposes an Orthanc User Interface on [http://localhost/orthanc/ui/app/](http://localhost/orthanc/ui/app/) accessible only
  to logged in users.
- a Postgresql container to store the Orthanc database
- an `orthanc-auth-service` web service that handles authorization and permissions
- a [KeyCloak](https://www.keycloak.org/) container handling authentication and providing user roles.

# Starting the setup

To start the setup, type: `./start-demo.sh`

# demo

## Using the UI

- Orthanc UI with full admin access is accessible at [http://localhost/orthanc/ui/app/](http://localhost/orthanc/ui/app/).  Login/pwd = `orthanc/orthanc`
- follow the instructions in this video to share a study

![Sharing a study in OE2](doc/Share-study.gif)


## Using the API

- upload a study, get its orthanc-id (through the API button: `copy study orthanc id`.  e.g: `ba19d592-4bb03a7b-65f06402-ae2b8ab1-6b33c7dc`), get its UID (through the clipboard icon)
- create a public share by issuing this command (`id` is optional and is dedicated to the client app):
```bash
curl -X PUT http://demo-script-user:demo-script-password@localhost:8000/shares -H 'Content-Type: application/json' \
  -d '{"id": "id_for_client_app",
       "studies" : [{
         "dicom-uid": "1.2.276.0.7230010.3.1.2.2344313775.14992.1458058359.6811", 
         "orthanc-id": "ba19d592-4bb03a7b-65f06402-ae2b8ab1-6b33c7dc"
       }],
       "anonymized": false, 
       "type": "stone-viewer-publication", 
       "expiration-date": "2022-12-31T11:00:00Z"}'
```
- then open the url from the response ([sample](http://localhost/welcome/?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6InRvdG8iLCJkaWNvbV91aWQiOiIxLjIuMjc2LjAuNzIzMDAxMC4zLjEuMi4yMzQ0MzEzNzc1LjE0OTkyLjE0NTgwNTgzNTkuNjgxMSIsIm9ydGhhbmNfaWQiOiJiYTE5ZDU5Mi00YmIwM2E3Yi02NWYwNjQwMi1hZTJiOGFiMS02YjMzYzdkYyIsImFub255bWl6ZWQiOmZhbHNlLCJ0eXBlIjoib3NpbWlzLXZpZXdlci1wdWJsaWNhdGlvbiIsImV4cGlyYXRpb25fZGF0ZSI6IjIwMjItMTItMzFUMTE6MDA6MDArMDA6MDAifQ.0uO1pUXm9ih81yCDKpaLqoIiuLJqdF66PIggmLI3Hoo)).
- the `orthanc-share-landing` service will then check that your token can be decoded and has not expired and then forward you to the viewer
- create an anonymized public share by issuing this command:
```bash
curl -X PUT http://demo-script-user:demo-script-password@localhost:8000/shares -H 'Content-Type: application/json' \
  -d '{"id": "demo-1", 
       "studies" : [{
         "dicom-uid": "1.2.276.0.7230010.3.1.2.2344313775.14992.1458058359.6811", 
         "orthanc-id": "ba19d592-4bb03a7b-65f06402-ae2b8ab1-6b33c7dc"
       }],
       "anonymized": true, 
       "type": "stone-viewer-publication", 
       "expiration-date": null}'
```
- then open the url from the response ([sample](http://localhost/welcome/?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6ImRlbW8tMSIsImRpY29tX3VpZCI6IjEuMi4yNzYuMC43MjMwMDEwLjMuMS4yLjIzNDQzMTM3NzUuMTQ5OTIuMTQ1ODA1ODM1OS42ODExIiwib3J0aGFuY19pZCI6ImJhMTlkNTkyLTRiYjAzYTdiLTY1ZjA2NDAyLWFlMmI4YWIxLTZiMzNjN2RjIiwiYW5vbnltaXplZCI6dHJ1ZSwidHlwZSI6Im9zaW1pcy12aWV3ZXItcHVibGljYXRpb24iLCJleHBpcmF0aW9uX2RhdGUiOm51bGx9.agqiD0EeD_DR4yboXIwsAN80ZjAZlgoey4-QxUkfAqU)). 
- the `orthanc-share-landing` service will then check that your token can be decoded and has not expired and then forward you to the viewer

# Users and roles management

There are 2 different locations to consider for users and roles management:
- the Keycloak management interface
- the configuration file
## Manage users and roles in Keycloak interface
The first step is the creation of users in keycloak web app (http://localhost:8080), the [Keycloak official documentation](https://www.keycloak.org/docs/latest/server_admin/index.html#assembly-managing-users_server_administration_guide) will give you all the information.
The current setup comes with 2 pre-defined users:
- orthanc
- doctor

The second step is the creation of roles in keycloak web app (http://localhost:8080), the [Keycloak official documentation](https://www.keycloak.org/docs/latest/server_admin/index.html#proc-creating-realm-roles_server_administration_guide) will give you all the information.
The current setup comes with 2 pref-defined roles:
- admin: this role is assigned to the `orthanc` user
- doctor: this role is assigned to the `doctor` user

## Manage permissions in the configuration file
The last step is the binding between roles and permissions.
This is done in the `permissions.json` file. Here is a sample:
```
{
  "roles" : {
    "admin": ["all"],
    "doctor": ["view", "download", "share", "send"]
  }
}
```
This file has to be provided to the `orthanc-auth-service` container via the env var `PERMISSIONS_FILE_PATH`.
Here is the list of available permissions:
```
all
view
download
delete
send
modify
anonymize
upload
q-r-remote-modalities
settings
api-view
share
```

# MedDream integration

To start the setup, type: `./start-demo-with-meddream.sh`

- A script or application requests the `orthanc-auth-service` web-service to generate a `meddream-instant-link` token via the Rest API:
```bash
curl -X PUT http://demo-script-user:demo-script-password@localhost:8000/shares -H 'Content-Type: application/json' \
  -d '{"id": "demo-1",
       "studies" : [{
         "dicom-uid": "1.2.276.0.7230010.3.1.2.2344313775.14992.1458058359.6811"
       }],
       "type": "meddream-instant-link"}'
```
- then open the url from the response ([sample](http://localhost/meddream/?token=B0VKYtVmPoa2Ye8IRLoc9GZ4SHf-02_DmHEFvlsvOm1TYmALSq9S56FiDG7_2t-XZJZXF_b-BVfDwlxWHLPfgaRxHULrkuuSaSHn1jx_c4Q7YLnQxbQ=)).

- A script or application may also requests the `orthanc-auth-service` web-service to generate a `meddream-viewer-publication` token via the Rest API:
```bash
curl -X PUT http://demo-script-user:demo-script-password@localhost:8000/shares -H 'Content-Type: application/json' \
  -d '{"id": "demo-1",
       "studies" : [{
         "dicom-uid": "1.2.276.0.7230010.3.1.2.2344313775.14992.1458058359.6811"
       },
       {
         "dicom-uid": "1.2.276.0.7230010.3.1.2.1215942821.4756.1664826045.3529"
       }],
       "type": "meddream-viewer-publication"}'
```
- then open the url from the response ([sample](http://localhost/welcome/?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6ImRlbW8tMSIsImRpY29tX3VpZCI6IjEuMi4yNzYuMC43MjMwMDEwLjMuMS4yLjIzNDQzMTM3NzUuMTQ5OTIuMTQ1ODA1ODM1OS42ODExIiwib3J0aGFuY19pZCI6bnVsbCwiYW5vbnltaXplZCI6ZmFsc2UsInR5cGUiOiJtZWRkcmVhbS12aWV3ZXItcHVibGljYXRpb24iLCJleHBpcmF0aW9uX2RhdGUiOm51bGx9.lW9gOWIABY-jigewbuxbELvRMbjffu2pS_MXCVKM3ts)).
- This will generate a temporary `meddream-instant-link` and will redirect you to the MedDream viewer.

# TLS handling
As soon as you want to handle TLS, you should:

- change all the passwords (don't forget the `master`realm)
- create the DNS record in your registrar configuration
- set `ENABLE_HTTPS` to `true`in the `nginx` service
- forward 443 port (in place of 80) in the `nginx`service
- bind some volumes to make cert and key available in the `nginx` service
- set `KC_HOSTNAME_URL` and `KC_HOSTNAME_ADMIN_URL` to the right value in the `keycloak` service
- set `Url` (in `OrthancExplorer2` - `Keycloak`) to the right value in the `orthanc` service (see `orthanc.jsonc` file)
- in the Keycloak web interface, set the `Valid redirect URIs` and `Web origins` values (see [official doc](https://www.keycloak.org/getting-started/getting-started-docker#_secure_the_first_application))