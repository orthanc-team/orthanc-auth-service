# orthanc-share

Web service to run next to orthanc to handle sharing of studies by issuing [JWT](https://jwt.io/) that can then be passed
in authorization headers that will be checked by the [Authorization plugin](https://book.orthanc-server.com/plugins/authorization.html).


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

## How to build and run

```bash
docker build -t orthanc-share .
docker run -p 8000:8000 --env SECRET_KEY=change-me --env PUBLIC_ORTHANC_ROOT=http://localhost:8042  orthanc-share
```