# orthanc-share
Web service to run next to orthanc to handle sharing of studies


sample request to get a share
```
curl -X PUT http://localhost:8000/shares -H 'Content-Type: application/json' \
  -d '{"id": "toto", 
       "dicom-uid": "1.2", 
       "orthanc-id": "0195f13e-4afe6822-8b494cc4-5162c50d-0daf66aa", 
       "type": "osimis-viewer-publication", 
       "expiration_date": "2022-07-07T11:00:00Z"}'
```

sample request to validate a auth token
```
curl -X POST http://localhost:8000/auth/validate -H 'token: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6InRvdG8iLCJkaWNvbV91aWQiOiIxLjIiLCJvcnRoYW5jX2lkIjoiMDE5NWYxM2UtNGFmZTY4MjItOGI0OTRjYzQtNTE2MmM1MGQtMGRhZjY2YWEiLCJ0eXBlIjoib3NpbWlzLXZpZXdlci1wdWJsaWNhdGlvbiIsImV4cGlyYXRpb25fZGF0ZSI6IjIwMjItMDctMDdUMTE6MDA6MDArMDA6MDAifQ.8mzvYXCrjhM8OWPhu5HQJbEtCO9y6XyFqV-Ak1n-9Tw' \
  -H 'Content-Type: application/json' \
  -d '{"dicom-uid": "1.2", 
       "orthanc-id": "6eeded74-75005003-c3ae9738-d4a06a4f-6beedeb8", 
       "level": "study", 
       "method": "get"}'
```
