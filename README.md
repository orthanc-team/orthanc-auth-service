# orthanc-share

Web service to run next to orthanc to handle sharing of studies by issuing [JWT](https://jwt.io/) that can then be passed
in authorization headers that will be checked by the [Authorization plugin](https://book.orthanc-server.com/plugins/authorization.html).

The Orthanc-share web service also allows generating links to open the MedDream viewer.

This repo also includes a reverse proxy that can perform on-the-fly anonymization of some Orthanc REST API routes.



## how it works ?

- `orthanc-share` is a webservice that generates `token` to grant access to a particular study in Orthanc.
- You must configure the `orthanc-share` web-service by providing at least 2 environment variables (or Docker secrets)
  - `SECRET_KEY` is a high entropy text that will be used to encode and decode the JWT
  - `PUBLIC_ORTHANC_ROOT` is the root url of the public Orthanc
- A script or application requests the `orthanc-share` web-service to generate such a token via the Rest API:
```bash
curl -X PUT http://localhost:8000/shares -H 'Content-Type: application/json' \
  -d '{"id": "toto", 
       "dicom-uid": "1.2", 
       "orthanc-id": "0195f13e-4afe6822-8b494cc4-5162c50d-0daf66aa", 
       "type": "osimis-viewer-publication", 
       "expiration_date": "2022-07-07T11:00:00Z"}'
```
- the `orthanc-share` replies with a share with the token and a link to the viewer:
```json
  {
    "request":{
      "id":"toto",
      "dicom-uid":"1.2",
      "orthanc-id":"0195f13e-4afe6822-8b494cc4-5162c50d-0daf66aa",
      "type":"osimis-viewer-publication",
      "expiration_date":"2022-07-07T11:00:00+00:00"
    },
    "token":"eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6InRvdG8iLCJkaWNvbV91aWQiOiIxLjIiLCJvcnRoYW5jX2lkIjoiMDE5NWYxM2UtNGFmZTY4MjItOGI0OTRjYzQtNTE2MmM1MGQtMGRhZjY2YWEiLCJ0eXBlIjoib3NpbWlzLXZpZXdlci1wdWJsaWNhdGlvbiIsImV4cGlyYXRpb25fZGF0ZSI6IjIwMjItMDctMDdUMTE6MDA6MDArMDA6MDAifQ.8mzvYXCrjhM8OWPhu5HQJbEtCO9y6XyFqV-Ak1n-9Tw",
    "url":"http://localhost:8042/osimis-viewer/app/index.html?study=0195f13e-4afe6822-8b494cc4-5162c50d-0daf66aa&token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6InRvdG8iLCJkaWNvbV91aWQiOiIxLjIiLCJvcnRoYW5jX2lkIjoiMDE5NWYxM2UtNGFmZTY4MjItOGI0OTRjYzQtNTE2MmM1MGQtMGRhZjY2YWEiLCJ0eXBlIjoib3NpbWlzLXZpZXdlci1wdWJsaWNhdGlvbiIsImV4cGlyYXRpb25fZGF0ZSI6IjIwMjItMDctMDdUMTE6MDA6MDArMDA6MDAifQ.8mzvYXCrjhM8OWPhu5HQJbEtCO9y6XyFqV-Ak1n-9Tw"
  }
```
- once the Viewer tries to access the study, the authorization plugin will issue a request to `orthanc-share` to validate the token.
  Since `orthanc-share` is the only one to know the secret key, it is able to validate the token to grant access to this particular study.

- sample request issued to `orthanc-share` to validate a token
```bash
curl -X POST http://localhost:8000/shares/validate -H 'token: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6InRvdG8iLCJkaWNvbV91aWQiOiIxLjIiLCJvcnRoYW5jX2lkIjoiMDE5NWYxM2UtNGFmZTY4MjItOGI0OTRjYzQtNTE2MmM1MGQtMGRhZjY2YWEiLCJ0eXBlIjoib3NpbWlzLXZpZXdlci1wdWJsaWNhdGlvbiIsImV4cGlyYXRpb25fZGF0ZSI6IjIwMjItMDctMDdUMTE6MDA6MDArMDA6MDAifQ.8mzvYXCrjhM8OWPhu5HQJbEtCO9y6XyFqV-Ak1n-9Tw' \
  -H 'Content-Type: application/json' \
  -d '{"dicom-uid": "1.2", 
       "orthanc-id": "0195f13e-4afe6822-8b494cc4-5162c50d-0daf66aa", 
       "level": "study", 
       "method": "get"}'
```
- in response, the `orthanc-share` will reply with this payload (required by the authorization plugin):
```json
  {
    "granted":false,
    "validity":60
  }
```

## Working with MedDream

- If you want to generate links to MedDream Viewer, you should also define:
  - `ENABLE_MEDDREAM_SHARES` to `true` to enable generating tokens that are valid for a long period.
  - `ENABLE_MEDDREAM_INSTANT_LINKS` to `true` to enable generating links to open the MedDreamViewer within a few minutes.
  - `PUBLIC_MEDDREAM_REDIRECT_ROOT` is required for long validity tokens (see below) 
  - `MEDDREAM_TOKEN_SERVICE_URL` is the url of the MedDream token web service (MedDream has its own webservice to generate short term tokens)
  - `PUBLIC_MEDDREAM_ROOT` is the public root url where the MedDream Viewer can be accessed 
- A script or application requests the `orthanc-share` web-service to generate such a token via the Rest API:
```bash
curl -X PUT http://localhost:8000/shares -H 'Content-Type: application/json' \
  -d '{"id": "toto", 
       "dicom-uid": "1.2", 
       "orthanc-id": "0195f13e-4afe6822-8b494cc4-5162c50d-0daf66aa", 
       "type": "meddream-viewer-publication", 
       "expiration_date": "2022-07-07T11:00:00Z"}'
```
  Allowed values for `type` are `meddream-instant-link` and `meddream-viewer-publication`.  The `expiration_date` is never used for `meddream-instant-link` since the validity is actually configured in the MedDream Token Service.
- if generating a `meddream-instant-link`, `orthanc-share` replies with a share with the token and a link to the MedDream viewer that shall be opened directly after (within a few minutes):
```json
  {
    "request":{
      "id":"toto",
      "dicom-uid":"1.2",
      "orthanc-id":null,
      "type":"meddream-instant-link",
      "expiration_date":null
    },
    "token":"eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6InRvdG8iLCJkaWNvbV91aWQiOiIxLjIiLCJvcnRoYW5jX2lkIjoiMDE5NWYxM2UtNGFmZTY4MjItOGI0OTRjYzQtNTE2MmM1MGQtMGRhZjY2YWEiLCJ0eXBlIjoib3NpbWlzLXZpZXdlci1wdWJsaWNhdGlvbiIsImV4cGlyYXRpb25fZGF0ZSI6IjIwMjItMDctMDdUMTE6MDA6MDArMDA6MDAifQ.8mzvYXCrjhM8OWPhu5HQJbEtCO9y6XyFqV-Ak1n-9Tw",
    "url":"http://localhost/meddream/?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6InRvdG8iLCJkaWNvbV91aWQiOiIxLjIiLCJvcnRoYW5jX2lkIjoiMDE5NWYxM2UtNGFmZTY4MjItOGI0OTRjYzQtNTE2MmM1MGQtMGRhZjY2YWEiLCJ0eXBlIjoib3NpbWlzLXZpZXdlci1wdWJsaWNhdGlvbiIsImV4cGlyYXRpb25fZGF0ZSI6IjIwMjItMDctMDdUMTE6MDA6MDArMDA6MDAifQ.8mzvYXCrjhM8OWPhu5HQJbEtCO9y6XyFqV-Ak1n-9Tw"
  }
```
- if generating a `meddream-viewer-publiction`, `orthanc-share` replies with a share with the token and a link to the `meddream redirect service` that will, once accessed, generate a new MedDream token that can be used within a few minutes:
```json
  {
    "request":{
      "id":"toto",
      "dicom-uid":"1.2",
      "orthanc-id":null,
      "type":"meddream-viewer-publication",
      "expiration_date":"2022-07-07T11:00:00Z"
    },
    "token":"eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6InRvdG8iLCJkaWNvbV91aWQiOiIxLjIiLCJvcnRoYW5jX2lkIjoiMDE5NWYxM2UtNGFmZTY4MjItOGI0OTRjYzQtNTE2MmM1MGQtMGRhZjY2YWEiLCJ0eXBlIjoib3NpbWlzLXZpZXdlci1wdWJsaWNhdGlvbiIsImV4cGlyYXRpb25fZGF0ZSI6IjIwMjItMDctMDdUMTE6MDA6MDArMDA6MDAifQ.8mzvYXCrjhM8OWPhu5HQJbEtCO9y6XyFqV-Ak1n-9Tw",
    "url":"http://localhost/meddream-redirect/?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6InRvdG8iLCJkaWNvbV91aWQiOiIxLjIiLCJvcnRoYW5jX2lkIjoiMDE5NWYxM2UtNGFmZTY4MjItOGI0OTRjYzQtNTE2MmM1MGQtMGRhZjY2YWEiLCJ0eXBlIjoib3NpbWlzLXZpZXdlci1wdWJsaWNhdGlvbiIsImV4cGlyYXRpb25fZGF0ZSI6IjIwMjItMDctMDdUMTE6MDA6MDArMDA6MDAifQ.8mzvYXCrjhM8OWPhu5HQJbEtCO9y6XyFqV-Ak1n-9Tw"
  }
```
- once the user tries to access the provided url, the `meddream-redirect-service` will reply with an HTTP redirect response redirecting the browser to the MedDreamViewer with a new token that is valid for a few minutes only.
- the `meddream-redirect-service` is actually also implemented by the `orthanc-share` web service.  A nginx reverse proxy positioned in front of this service shall ensure that only the `/meddream-redirect` route is accessible from the exterior.


## Docker images

This repo builds a few images that can be reused directly and published on Dockerhub.

- `orthanc-share` is the webservice generating and validating tokens and also implements the `meddream-redirect-service`.
- `orthanc-anonymizer` is a reverse-proxy that performs on-the-fly anonymization of the Orthanc Rest API routes that are used by the Osimis Viewer.
- `meddream-viewer` is a pre-configured version of the [meddream:orthanc-dicom-viewer](https://hub.docker.com/r/meddream/orthanc-dicom-viewer) image
- `meddream-token-service` is a pre-configured version of the [meddream:token-service](https://hub.docker.com/r/meddream/token-service) image


```bash
docker build -t orthanc-share .
docker run -p 8000:8000 --env SECRET_KEY=change-me --env PUBLIC_ORTHANC_ROOT=http://localhost:8042  orthanc-share
```