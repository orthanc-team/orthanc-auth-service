<!--
SPDX-FileCopyrightText: 2022 - 2025 Orthanc Team SRL <info@orthanc.team>

SPDX-License-Identifier: CC-BY-4.0
-->

[![REUSE status](https://api.reuse.software/badge/github.com/orthanc-team/orthanc-share)](https://api.reuse.software/info/github.com/orthanc-team/orthanc-share)

# orthanc-auth-service

This repository contains web services to run next to orthanc to handle user permissions through an integration with [Keycloak](keycloak.org) 
and secure sharing of studies by issuing [JWT](https://jwt.io/) that can then be passed
in authorization headers.  The HTTP headers are then checked by the [Orthanc authorization plugin](https://book.orthanc-server.com/plugins/authorization.html) to validate the access.

These web services integrates with [Orthanc Explorer 2](https://book.orthanc-server.com/plugins/orthanc-explorer-2.html).

This initial solution for study sharing has been [presented](https://orthanc.team/files/doc/OrthancCon2022-Sharing-DICOM-studies-with-Orthanc.pdf) at [OrthancCon 2022](https://www.orthanc-server.com/static.php?page=orthanc-con-2022).
The user permissions handling was not available at that time.

Features:
- Handles user authentication & permissions together with Keycloak
- Generates publication links for:
  - [Stone Viewer](https://www.orthanc-server.com/static.php?page=stone-web-viewer)
  - [OHIF Viewer](https://ohif.org/)
  - [MedDream Viewer](https://www.softneta.com/online-dicom-viewer/) (commercial - CE approved)
- 3 Boilerplates `docker-compose` setups to bootstrap a setup:
  - One with [basic authentication](minimal-setup/basic-auth) only to demonstrate study sharing.
  - One with [Keycloak integration](minimal-setup/keycloak) to demonstrate user management and study sharing
  - One full setup with [Keycloak, MedDream and Orthanc for API](minimal-setup/keycloak) to demonstrate user management, study sharing, MedDream usage and an extra orthanc accessible e.g by DicomWebClient.
- provides a set of companion docker images to ease deployment:
  - [orthancteam/orthanc-aut-service](https://hub.docker.com/r/orthancteam/orthanc-auth-service) is the webservice generating and validating tokens.  The web service is also providing user permissions from Keycloak defined roles.
  - [orthancteam/orthanc-nginx](https://hub.docker.com/r/orthancteam/orthanc-nginx)
  - [orthancteam/orthanc-keycloak](https://hub.docker.com/r/orthancteam/orthanc-keycloak)
  - [orthancteam/meddream-token-service](https://hub.docker.com/r/orthancteam/meddream-token-service) is a pre-configured version of the [meddream:token-service](https://hub.docker.com/r/meddream/token-service) image
  - [orthancteam/meddream-viewer](https://hub.docker.com/r/orthancteam/meddream-viewer) is a pre-configured version of the [meddream:orthanc-dicom-viewer](https://hub.docker.com/r/meddream/orthanc-dicom-viewer) image


![Sharing a study in OE2](./demo-setup/doc/Share-study.gif)


## Release notes

Check the [release notes](release-notes.md).


# Users and roles management

There are 2 different locations to consider for users and roles management:
- the Keycloak management interface
- the configuration file

## Manage users and roles in Keycloak interface

The first step is the creation of users in keycloak web app (http://localhost/keycloak/), the [Keycloak official documentation](https://www.keycloak.org/docs/latest/server_admin/index.html#assembly-managing-users_server_administration_guide) will give you all the information.
The current setup comes with 2 pre-defined users:
- `orthanc`
- `doctor`

And 2 pre-defined roles:
- `admin`: this role is assigned to the `orthanc` user
- `doctor`: this role is assigned to the `doctor` user

## Manage permissions in the configuration file

The last step is the binding between roles and permissions.
This is done in the `permissions.json` file. Here is the default file:
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

These permissions are also configured in the Orthanc authorization plugin (in the `Authorization.Permissions` configuration).
The [default configuration](https://hg.orthanc-server.com/orthanc-authorization/file/tip/Plugin/DefaultConfiguration.json) is suitable to work with this sample.


## how it works (internals) ?

- `orthanc-auth-service` is a web service that generates `token` to grant access to a particular study in Orthanc.
  - You must configure the `orthanc-auth-service` web-service by providing these environment variables (or Docker secrets)
    - `SECRET_KEY` is a high entropy text that will be used to encode and decode the JWT
    - To enable orthanc standard shares (without anonymization):
      - `PUBLIC_ORTHANC_ROOT` is the root url of the public Orthanc
      - `PUBLIC_LANDING_ROOT` is the url of a OE2 page that will display a message to the user when the token has expired or is invalid
      - `SERVER_ID` is the identifier defined in the Authorization plugin configuration of the standard Orthanc (optional)
    - `USERS` is an optional environment variable that should contain a json array of allowed usernames/passwords to access the service.
      ```json
      {
        "user1": "pwd1",
        "user2": "pwd2"
      }
      ```
      If not defined, the token-service is available without authentication.  If you expose the web-service publicly, you should always configure authentication.
- A script or application requests the `orthanc-auth-service` to generate such a token via the Rest API:
```bash
curl -X PUT http://localhost:8000/tokens/stone-viewer-publication -H 'Content-Type: application/json' \
  -d '{"id": "toto",
       "resources" : [{
         "dicom-uid": "1.2",
         "level": "study"
       }],
       "type": "stone-viewer-publication", 
       "expiration-date": "2026-12-31T11:00:00Z"}'
```
  Note that a user that is authenticated to Orthanc and that has the permission to access this url can also call
  the auth-plugin directly with an orthanc flavored API call:
```bash
curl -X PUT http://localhost:8042/auth/tokens/stone-viewer-publication -H 'Content-Type: application/json' \
  -d '{"ID": "toto",
       "Resources" : [{
         "dicom-uid": "1.2",
         "orthanc-id": "",
         "level": "study"
       }],
       "type": "stone-viewer-publication", 
       "expiration-date": "2026-12-31T11:00:00Z"}'
```


- the `orthanc-auth-service` replies with a share with the token and a link to the viewer:
```json
  {
    "request":{
      "id":"toto",
      "resources" : [
        {
          "dicom-uid": "1.2"
        }],  
      "type":"stone-viewer-publication",
      "expiration-date":"2026-07-07T11:00:00+00:00"
    },
    "token":"eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6InRvdG8iLCJyZXNvdXJjZXMiOlt7ImRpY29tX3VpZCI6IjEuMiIsIm9ydGhhbmNfaWQiOm51bGwsInVybCI6bnVsbCwibGV2ZWwiOiJzdHVkeSJ9XSwidHlwZSI6InN0b25lLXZpZXdlci1wdWJsaWNhdGlvbiIsImV4cGlyYXRpb25fZGF0ZSI6IjIwMjYtMTItMzFUMTE6MDA6MDArMDA6MDAifQ.RlB9x56eQSaJNt3t4hDxAHdM7BhBbah5CWWBBZQf7x0",
    "url":"http://localhost/ui/app/token-landing.html?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6InRvdG8iLCJyZXNvdXJjZXMiOlt7ImRpY29tX3VpZCI6IjEuMiIsIm9ydGhhbmNfaWQiOm51bGwsInVybCI6bnVsbCwibGV2ZWwiOiJzdHVkeSJ9XSwidHlwZSI6InN0b25lLXZpZXdlci1wdWJsaWNhdGlvbiIsImV4cGlyYXRpb25fZGF0ZSI6IjIwMjYtMTItMzFUMTE6MDA6MDArMDA6MDAifQ.RlB9x56eQSaJNt3t4hDxAHdM7BhBbah5CWWBBZQf7x0"
  }
```
- once the users clicks on this link, the `token-landing` page will check the token validity and redirect the browser
  to the Stone Viewer
- once the Viewer tries to access the study, the authorization plugin will issue a request to `orthanc-auth-service` to validate the token.
  Since `orthanc-auth-service` is the only one to know the secret key, it is able to validate the token to grant access to this particular study.

- sample request issued to `orthanc-auth-service` to validate a token
```bash
curl -X POST http://localhost:8000/tokens/validate -H 'token: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6InRvdG8iLCJyZXNvdXJjZXMiOlt7ImRpY29tX3VpZCI6IjEuMiIsIm9ydGhhbmNfaWQiOm51bGwsInVybCI6bnVsbCwibGV2ZWwiOiJzdHVkeSJ9XSwidHlwZSI6InN0b25lLXZpZXdlci1wdWJsaWNhdGlvbiIsImV4cGlyYXRpb25fZGF0ZSI6IjIwMjYtMTItMzFUMTE6MDA6MDArMDA6MDAifQ.RlB9x56eQSaJNt3t4hDxAHdM7BhBbah5CWWBBZQf7x0' \
  -H 'Content-Type: application/json' \
  -d '{"dicom-uid": "1.2", 
       "orthanc-id": "0195f13e-4afe6822-8b494cc4-5162c50d-0daf66aa",
       "server-id": "server-id", 
       "level": "study", 
       "method": "get"}'
```
- in response, the `orthanc-auth-service` will reply with this payload (required by the authorization plugin):
```json
  {
    "granted":false,
    "validity":60
  }
```

## Working with MedDream

- If you want to generate links to MedDream Viewer, you should also define:
  - `MEDDREAM_TOKEN_SERVICE_URL` is the url of the MedDream token web service (MedDream has its own webservice to generate short term tokens)
  - `PUBLIC_MEDDREAM_ROOT` is the public root url where the MedDream Viewer can be accessed 
- A script or application requests the `orthanc-auth-service` to generate such a token via the Rest API:
```bash
curl -X PUT http://localhost:8000/tokens/meddream-instant-link -H 'Content-Type: application/json' \
-d '{"id": "toto",
       "resources" : [{
         "dicom-uid": "1.2.276.0.37.1.322.201502.11033927",
         "level": "study"
       }],
       "type": "meddream-instant-link", 
       "expiration-date": "2026-12-31T11:00:00Z"}'
```
  Allowed values for `type` are `meddream-instant-link` and `meddream-viewer-publication`.  The `expiration-date` is 
  never used for `meddream-instant-link` since the validity is actually configured in the MedDream Token Service.
  Route has to be adapted to fit the type, for a publication: `curl -X PUT http://localhost:8000/tokens/meddream-viewer-publication...`
- if generating a `meddream-instant-link`, `orthanc-auth-service` replies with a share with the token and a link to the 
  MedDream viewer that shall be opened directly after (within a few minutes):
```json
{
  "request":{
    "id":"demo-1",
    "resources":[{
      "dicom-uid":"1.2.276.0.37.1.322.201502.11033927",
      "orthanc-id":null,
      "url":null,
      "level":"study"
    }],
    "type":"meddream-instant-link",
    "expiration-date":null,
    "validity-duration":null},
  "token":"7VwozctM_1wdeYTyhCaSLi_PfVU7sn9ZVDd2h6Ilo7SlhZAinEa-oFFdfzeNN8J9zCWGEGTHsy0hqPishc7eLg-kqgx9N5LqNT5hZl8LTXAxL3zTIw4=",
  "url":"http://localhost/meddream/?study=1.2.276.0.37.1.322.201502.11033927&token=7VwozctM_1wdeYTyhCaSLi_PfVU7sn9ZVDd2h6Ilo7SlhZAinEa-oFFdfzeNN8J9zCWGEGTHsy0hqPishc7eLg-kqgx9N5LqNT5hZl8LTXAxL3zTIw4="
}

```
- if generating a `meddream-viewer-publication`, `orthanc-auth-service` replies with a share with the token and a link to the `token-landing` page that will, once accessed, generate a new MedDream token that can be used within a few minutes:
```json
{
  "request":{
    "id":"demo-1",
    "resources":[{
      "dicom-uid":"1.2.276.0.37.1.322.201502.11033927",
      "orthanc-id":null,
      "url":null,
      "level":"study"}],
    "type":"meddream-viewer-publication",
    "expiration-date":null,
    "validity-duration":null},
  "token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ImRlbW8tMSIsInJlc291cmNlcyI6W3siZGljb21fdWlkIjoiMS4yLjI3Ni4wLjM3LjEuMzIyLjIwMTUwMi4xMTAzMzkyNyIsIm9ydGhhbmNfaWQiOm51bGwsInVybCI6bnVsbCwibGV2ZWwiOiJzdHVkeSJ9XSwidHlwZSI6Im1lZGRyZWFtLXZpZXdlci1wdWJsaWNhdGlvbiIsImV4cGlyYXRpb25fZGF0ZSI6bnVsbCwidmFsaWRpdHlfZHVyYXRpb24iOm51bGx9.a2189RYDjlPueJ8QkquJylVJCOXDRyCltGcalnkyJQM",
  "url":"http://localhost/orthanc/ui/app/token-landing.html?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ImRlbW8tMSIsInJlc291cmNlcyI6W3siZGljb21fdWlkIjoiMS4yLjI3Ni4wLjM3LjEuMzIyLjIwMTUwMi4xMTAzMzkyNyIsIm9ydGhhbmNfaWQiOm51bGwsInVybCI6bnVsbCwibGV2ZWwiOiJzdHVkeSJ9XSwidHlwZSI6Im1lZGRyZWFtLXZpZXdlci1wdWJsaWNhdGlvbiIsImV4cGlyYXRpb25fZGF0ZSI6bnVsbCwidmFsaWRpdHlfZHVyYXRpb24iOm51bGx9.a2189RYDjlPueJ8QkquJylVJCOXDRyCltGcalnkyJQM"
}
```
- once the user tries to access the provided url, the `token-landing` page will reply with an HTTP redirect response redirecting the browser to the MedDreamViewer with a new token that is valid for a few minutes only.


## updating settings (internals) ?

Specific users with the right permissions can read/update the permissions configuration directly from OE2, through the `authorization-plugin` that forwards
the call to the `orthanc-auth-service`

```bash
curl -u share-user:change-me http://localhost:8000/settings/roles
```

```bash
curl -u share-user:change-me -H "Content-Type: application/json" http://localhost:8000/settings/roles -d '{"roles":{"admin-role":{"authorized-labels":["*"],"permissions":["all"]},"doctor-role":{"authorized-labels":["*"],"permissions":["view","download","share","send"]},"external-role":{"authorized-labels":["external"],"permissions":["view","download"]}},"available-labels":[]}'
```