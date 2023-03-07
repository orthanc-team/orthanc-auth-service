<!--
SPDX-FileCopyrightText: 2019 Jane Doe <jane@example.com>

SPDX-License-Identifier: GPL-3.0-or-later
-->

[![REUSE status](https://api.reuse.software/badge/github.com/orthanc-team/orthanc-share)](https://api.reuse.software/info/github.com/orthanc-team/orthanc-share)

# orthanc-share

This repository contains a set of web services to run next to orthanc to handle secure sharing of studies by issuing [JWT](https://jwt.io/) that can then be passed
in authorization headers.  The HTTP headers are then checked by the [Orthanc authorization plugin](https://book.orthanc-server.com/plugins/authorization.html) to validate the access.

These web services integrates with [Orthanc Explorer 2](https://book.orthanc-server.com/plugins/orthanc-explorer-2.html).

This solution has been [presented](https://orthanc.team/files/doc/OrthancCon2022-Sharing-DICOM-studies-with-Orthanc.pdf) at [OrthancCon 2022](https://www.orthanc-server.com/static.php?page=orthanc-con-2022).

Features:
- `orthanc-auth-service` to generate & validate tokens
- `orthanc-share-landing` to display user friendly messages if tokens are invalid
- Generates publication links for:
  - [Stone Viewer](https://www.orthanc-server.com/static.php?page=stone-web-viewer)
  - [Osimis Viewer](https://book.orthanc-server.com/plugins/osimis-webviewer.html)
  - [MedDream Viewer](https://www.softneta.com/online-dicom-viewer/) (commercial - CE approved)
- Handles expiration date
- `orthanc-anonymizer` to handle anonymized publications (still experimental, only works with the Osimis Viewer)
- Full [demo setup](./demo-setup) including integration with Orthanc Explorer 2
- Boilerplate [docker-compose.yml](minimal-setup/docker-compose.yml) to bootstrap a setup
- Used in production


![Sharing a study in OE2](./demo-setup/doc/Share-study.gif)


## how it works ?

- `orthanc-auth-service` is a web service that generates `token` to grant access to a particular study in Orthanc.
  - You must configure the `orthanc-auth-service` web-service by providing these environment variables (or Docker secrets)
    - `SECRET_KEY` is a high entropy text that will be used to encode and decode the JWT
    - To enable orthanc standard shares (without anonymization):
      - `PUBLIC_ORTHANC_ROOT` is the root url of the public Orthanc
      - `SERVER_ID` is the identifier defined in the Authorization plugin configuration of the standard Orthanc (not required if not allowing anonymized shares)
    - To enable orthanc anonymized shares, you should define these additionnal environment variables:
      - `PUBLIC_ANONYMIZED_ORTHANC_ROOT` is the root url of the public anonymized Orthanc
    - `USERS` is an optional environment variable that should contain a json array of allowed usernames/passwords to access the service.
      ```json
      {
        "user1": "pwd1",
        "user2": "pwd2"
      }
      ```
      If not defined, the token-service is available without authentication.  If you expose the web-service publicly, you should always configure authentication.
- If you want to display a message to the user when the token has expired or is invalid, you should also define 
  `PUBLIC_LANDING_ROOT` pointing to the `orthanc-share-landing` web service that must be configured with the same
  environment variables as the `orthanc-auth-service`.
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
         "DicomUid": "1.2",
         "OrthancId": "",
         "Level": "study"
       }],
       "Type": "stone-viewer-publication", 
       "ExpirationDate": "2026-12-31T11:00:00Z"}'
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
    "url":"http://localhost/welcom/?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6InRvdG8iLCJyZXNvdXJjZXMiOlt7ImRpY29tX3VpZCI6IjEuMiIsIm9ydGhhbmNfaWQiOm51bGwsInVybCI6bnVsbCwibGV2ZWwiOiJzdHVkeSJ9XSwidHlwZSI6InN0b25lLXZpZXdlci1wdWJsaWNhdGlvbiIsImV4cGlyYXRpb25fZGF0ZSI6IjIwMjYtMTItMzFUMTE6MDA6MDArMDA6MDAifQ.RlB9x56eQSaJNt3t4hDxAHdM7BhBbah5CWWBBZQf7x0"
  }
```
- once the users clicks on this link, the `orthanc-share-landing` will check the token validity and redirect the browser
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
  - `PUBLIC_LANDING_ROOT` is required for long validity tokens (see below) 
  - `MEDDREAM_TOKEN_SERVICE_URL` is the url of the MedDream token web service (MedDream has its own webservice to generate short term tokens)
  - `PUBLIC_MEDDREAM_ROOT` is the public root url where the MedDream Viewer can be accessed 
- A script or application requests the `orthanc-auth-service` to generate such a token via the Rest API:
```bash
curl -X PUT http://localhost:8000/shares -H 'Content-Type: application/json' \
  -d '{"id": "toto",
       "studies" : [{
         "dicom-uid": "1.2"
       }],
       "type": "meddream-viewer-publication", 
       "expiration-date": "2022-07-07T11:00:00Z"}'
```
  Allowed values for `type` are `meddream-instant-link` and `meddream-viewer-publication`.  The `expiration-date` is 
  never used for `meddream-instant-link` since the validity is actually configured in the MedDream Token Service.
- if generating a `meddream-instant-link`, `orthanc-auth-service` replies with a share with the token and a link to the 
  MedDream viewer that shall be opened directly after (within a few minutes):
```json
  {
    "request":{
      "id":"toto",
      "studies" : [
        {
          "dicom-uid": "1.2",
          "orthanc-id": null
        }],  
      "type":"meddream-instant-link",
      "expiration-date":null
    },
    "token":"eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6InRvdG8iLCJkaWNvbV91aWQiOiIxLjIiLCJvcnRoYW5jX2lkIjoiMDE5NWYxM2UtNGFmZTY4MjItOGI0OTRjYzQtNTE2MmM1MGQtMGRhZjY2YWEiLCJ0eXBlIjoib3NpbWlzLXZpZXdlci1wdWJsaWNhdGlvbiIsImV4cGlyYXRpb25fZGF0ZSI6IjIwMjItMDctMDdUMTE6MDA6MDArMDA6MDAifQ.8mzvYXCrjhM8OWPhu5HQJbEtCO9y6XyFqV-Ak1n-9Tw",
    "url":"http://localhost/meddream/?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6InRvdG8iLCJkaWNvbV91aWQiOiIxLjIiLCJvcnRoYW5jX2lkIjoiMDE5NWYxM2UtNGFmZTY4MjItOGI0OTRjYzQtNTE2MmM1MGQtMGRhZjY2YWEiLCJ0eXBlIjoib3NpbWlzLXZpZXdlci1wdWJsaWNhdGlvbiIsImV4cGlyYXRpb25fZGF0ZSI6IjIwMjItMDctMDdUMTE6MDA6MDArMDA6MDAifQ.8mzvYXCrjhM8OWPhu5HQJbEtCO9y6XyFqV-Ak1n-9Tw"
  }
```
- if generating a `meddream-viewer-publication`, `orthanc-auth-service` replies with a share with the token and a link to the `meddream redirect service` that will, once accessed, generate a new MedDream token that can be used within a few minutes:
```json
  {
    "request":{
      "id":"toto",
      "studies" : [
        {
          "dicom-uid": "1.2",
          "orthanc-id": null
        }],  
      "type":"meddream-viewer-publication",
      "expiration-date":"2022-07-07T11:00:00Z"
    },
    "token":"eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6InRvdG8iLCJkaWNvbV91aWQiOiIxLjIiLCJvcnRoYW5jX2lkIjoiMDE5NWYxM2UtNGFmZTY4MjItOGI0OTRjYzQtNTE2MmM1MGQtMGRhZjY2YWEiLCJ0eXBlIjoib3NpbWlzLXZpZXdlci1wdWJsaWNhdGlvbiIsImV4cGlyYXRpb25fZGF0ZSI6IjIwMjItMDctMDdUMTE6MDA6MDArMDA6MDAifQ.8mzvYXCrjhM8OWPhu5HQJbEtCO9y6XyFqV-Ak1n-9Tw",
    "url":"http://localhost/welcom/?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6InRvdG8iLCJkaWNvbV91aWQiOiIxLjIiLCJvcnRoYW5jX2lkIjoiMDE5NWYxM2UtNGFmZTY4MjItOGI0OTRjYzQtNTE2MmM1MGQtMGRhZjY2YWEiLCJ0eXBlIjoib3NpbWlzLXZpZXdlci1wdWJsaWNhdGlvbiIsImV4cGlyYXRpb25fZGF0ZSI6IjIwMjItMDctMDdUMTE6MDA6MDArMDA6MDAifQ.8mzvYXCrjhM8OWPhu5HQJbEtCO9y6XyFqV-Ak1n-9Tw"
  }
```
- once the user tries to access the provided url, the `orthanc-share-landing` will reply with an HTTP redirect response redirecting the browser to the MedDreamViewer with a new token that is valid for a few minutes only.


## Docker images

This repo builds a few images that can be reused directly and published on Dockerhub.

- [orthancteam/orthanc-auth-service](https://hub.docker.com/repository/docker/orthancteam/orthanc-auth-service) is the webservice generating and validating tokens.
- [orthancteam/orthanc-share-landing](https://hub.docker.com/repository/docker/orthancteam/orthanc-share-landing) is the webservice providing error messages to the user and/or redirecting to MedDream, the StoneViewer or the OsimisViewer.
- [orthancteam/orthanc-anonymizer](https://hub.docker.com/repository/docker/orthancteam/orthanc-anonymizer) is a reverse-proxy that performs on-the-fly anonymization of the Orthanc Rest API routes that are used by the Osimis Viewer.
- [orthancteam/meddream-viewer](https://hub.docker.com/repository/docker/orthancteam/meddream-viewer) is a pre-configured version of the [meddream:orthanc-dicom-viewer](https://hub.docker.com/r/meddream/orthanc-dicom-viewer) image
- [orthancteam/meddream-token-service](https://hub.docker.com/repository/docker/orthancteam/meddream-token-service) is a pre-configured version of the [meddream:token-service](https://hub.docker.com/r/meddream/token-service) image

Check the [demo setup](./demo-setup/) for more info.

Check the [release notes](release-notes.md).