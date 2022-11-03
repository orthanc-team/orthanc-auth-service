# Purpose

This is a sample setup to demonstrate how to run Orthanc-Explorer-2 together with the `orthanc-share`
web-service to provide publication links to specific studies.

**Disclaimer**: this sample is provided 'as is' without any guarantee.  Don't use it in production unless you perfectly understand every part of it.

# Description

This demo contains:

- a nginx container that provides a web server on port 80.  It exposes the 3 Orthanc instances:
  - [/orthanc-admin/](http://localhost/orthanc-admin/ui/app/) is used by admin users who have access to all studies.
  - The second orthanc is used only for shared studies.  The UI is blocked as well as many routes.  This orthanc is using the Authorization plugin to validate tokens.
  - The third orthanc is used only for anonymized shared studies.  It is positioned behind an `orthanc-anonymizer`

- 3 Orthanc containers, one configured for `admin`, one configured for `shares` and one for anonymized `shares`
- a Postgresql container to store the Orthanc database
- an `orthanc-share` web service that generates publication link (listens on port 8000)
- an `orthanc-anonymizer` web service that performs on-the-fly anonymization of the Orthanc Rest API that is used by the OsimisViewer.

# Starting the setup

To start the setup, type: `./start-demo.sh`

# demo

## Using the UI

- Orthanc UI with full admin access is accessible at [http://localhost/orthanc-admin/ui/app/](http://localhost/orthanc-admin/ui/app/).  Login/pwd = `admin/admin`
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


# MedDream integration

To start the setup, type: `./start-demo-with-meddream.sh`

- A script or application requests the `orthanc-token-service` web-service to generate a `meddream-instant-link` token via the Rest API:
```bash
curl -X PUT http://demo-script-user:demo-script-password@localhost:8000/shares -H 'Content-Type: application/json' \
  -d '{"id": "demo-1",
       "studies" : [{
         "dicom-uid": "1.2.276.0.7230010.3.1.2.2344313775.14992.1458058359.6811"
       }],
       "type": "meddream-instant-link"}'
```
- then open the url from the response ([sample](http://localhost/meddream/?token=B0VKYtVmPoa2Ye8IRLoc9GZ4SHf-02_DmHEFvlsvOm1TYmALSq9S56FiDG7_2t-XZJZXF_b-BVfDwlxWHLPfgaRxHULrkuuSaSHn1jx_c4Q7YLnQxbQ=)).

- A script or application may also requests the `orthanc-token-service` web-service to generate a `meddream-viewer-publication` token via the Rest API:
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