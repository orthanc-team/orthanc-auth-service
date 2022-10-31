# orthanc-share

Web services to run next to orthanc to handle sharing of studies by issuing [JWT](https://jwt.io/) that can then be passed
in authorization headers that will be checked by the [Authorization plugin](https://book.orthanc-server.com/plugins/authorization.html).

The web services also allows generating links to open the MedDream viewer.

This repo also includes a reverse proxy that can perform on-the-fly anonymization of some Orthanc REST API routes.



## how it works ?

- `orthanc-token-service` is a web service that generates `token` to grant access to a particular study in Orthanc.
  - You must configure the `orthanc-token-service` web-service by providing these environment variables (or Docker secrets)
    - `SECRET_KEY` is a high entropy text that will be used to encode and decode the JWT
    - To enable orthanc standard shares (without anonymization):
      - `PUBLIC_ORTHANC_ROOT` is the root url of the public Orthanc
      - `SERVER_IDENTIFIER` is the identifier defined in the Authorization plugin configuration of the standard Orthanc (not required if not allowing anonymized shares)
    - To enable orthanc anonymized shares, you should define these additionnal environment variables:
      - `PUBLIC_ANONYMIZED_ORTHANC_ROOT` is the root url of the public anonymized Orthanc
      - `ANONYMIZED_SERVER_IDENTIFIER` is the identifier defined in the Authorization plugin configuration of the anonymized Orthanc
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
  environment variables as the `orthanc-token-service`.
- A script or application requests the `orthanc-token-service` to generate such a token via the Rest API:
```bash
curl -X PUT http://localhost:8000/shares -H 'Content-Type: application/json' \
  -d '{"id": "toto",
       "studies" : [{
         "orthanc-id": "ba19d592-4bb03a7b-65f06402-ae2b8ab1-6b33c7dc"
       }],
       "anonymized": true, 
       "type": "osimis-viewer-publication", 
       "expiration-date": "2022-12-31T11:00:00Z"}'
```
- the `orthanc-token-service` replies with a share with the token and a link to the viewer:
```json
  {
    "request":{
      "id":"toto",
      "studies" : [
        {
          "orthanc-id": "0195f13e-4afe6822-8b494cc4-5162c50d-0daf66aa"
        }],  
      "type":"osimis-viewer-publication",
      "expiration-date":"2022-07-07T11:00:00+00:00"
    },
    "token":"eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6InRvdG8iLCJkaWNvbV91aWQiOiIxLjIiLCJvcnRoYW5jX2lkIjoiMDE5NWYxM2UtNGFmZTY4MjItOGI0OTRjYzQtNTE2MmM1MGQtMGRhZjY2YWEiLCJ0eXBlIjoib3NpbWlzLXZpZXdlci1wdWJsaWNhdGlvbiIsImV4cGlyYXRpb25fZGF0ZSI6IjIwMjItMDctMDdUMTE6MDA6MDArMDA6MDAifQ.8mzvYXCrjhM8OWPhu5HQJbEtCO9y6XyFqV-Ak1n-9Tw",
    "url":"http://localhost/welcom/?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6InRvdG8iLCJkaWNvbV91aWQiOiIxLjIiLCJvcnRoYW5jX2lkIjoiMDE5NWYxM2UtNGFmZTY4MjItOGI0OTRjYzQtNTE2MmM1MGQtMGRhZjY2YWEiLCJ0eXBlIjoib3NpbWlzLXZpZXdlci1wdWJsaWNhdGlvbiIsImV4cGlyYXRpb25fZGF0ZSI6IjIwMjItMDctMDdUMTE6MDA6MDArMDA6MDAifQ.8mzvYXCrjhM8OWPhu5HQJbEtCO9y6XyFqV-Ak1n-9Tw"
  }
```
- once the users clicks on this link, the `orthanc-share-landing` will check the token validity and redirect the browser
  to the Osimis Viewer
- once the Viewer tries to access the study, the authorization plugin will issue a request to `orthanc-token-service` to validate the token.
  Since `orthanc-token-service` is the only one to know the secret key, it is able to validate the token to grant access to this particular study.

- sample request issued to `orthanc-token-service` to validate a token
```bash
curl -X POST http://localhost:8000/shares/validate -H 'token: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6InRvdG8iLCJkaWNvbV91aWQiOiIxLjIiLCJvcnRoYW5jX2lkIjoiMDE5NWYxM2UtNGFmZTY4MjItOGI0OTRjYzQtNTE2MmM1MGQtMGRhZjY2YWEiLCJhbm9ueW1pemVkIjp0cnVlLCJ0eXBlIjoib3NpbWlzLXZpZXdlci1wdWJsaWNhdGlvbiIsImV4cGlyYXRpb25fZGF0ZSI6IjIwMjItMTItMzFUMTE6MDA6MDArMDA6MDAifQ.vQPmlhoVQHUlbXg-JGenBIGQbNU0DhWXJPMdCMzBTFg' \
  -H 'Content-Type: application/json' \
  -d '{"dicom-uid": null, 
       "orthanc-id": "0195f13e-4afe6822-8b494cc4-5162c50d-0daf66aa",
       "identifier": "anonymized-server-id", 
       "level": "study", 
       "method": "get"}'
```
- in response, the `orthanc-token-service` will reply with this payload (required by the authorization plugin):
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
- A script or application requests the `orthanc-token-service` to generate such a token via the Rest API:
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
- if generating a `meddream-instant-link`, `orthanc-token-service` replies with a share with the token and a link to the 
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
- if generating a `meddream-viewer-publication`, `orthanc-token-service` replies with a share with the token and a link to the `meddream redirect service` that will, once accessed, generate a new MedDream token that can be used within a few minutes:
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

- `orthanc-token-service` is the webservice generating and validating tokens.
- `orthanc-share-landing` is the webservice providing error messages to the user and/or redirecting to MedDream or the OsimisViewer.
- `orthanc-anonymizer` is a reverse-proxy that performs on-the-fly anonymization of the Orthanc Rest API routes that are used by the Osimis Viewer.
- `meddream-viewer` is a pre-configured version of the [meddream:orthanc-dicom-viewer](https://hub.docker.com/r/meddream/orthanc-dicom-viewer) image
- `meddream-token-service` is a pre-configured version of the [meddream:token-service](https://hub.docker.com/r/meddream/token-service) image


Check the [demo setup](./demo-setup/) for more info.