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
- an `orthanc-share` web service that generates publication link for anonymized shares (listens on port 8001)
- an `orthanc-anonymizer` web service that performs on-the-fly anonymization of Orthanc Rest API.

# Starting the setup

To start the setup, type: `docker-compose up --build`

# demo

- Orthanc UI with full admin access is accessible at [http://localhost/orthanc-admin/ui/app/](http://localhost/orthanc-admin/ui/app/).  Login/pwd = `admin/admin`
- upload a study, get its orthanc-id (through the API button: `copy study orthanc id`.  e.g: `ba19d592-4bb03a7b-65f06402-ae2b8ab1-6b33c7dc`)
- create a public share by issuing this command:
```bash
curl -X PUT http://localhost:8000/shares -H 'Content-Type: application/json' \
  -d '{"id": "demo-1", 
       "dicom-uid": "1.2.276.0.7230010.3.1.2.2344313775.14992.1458058359.6811", 
       "orthanc-id": "ba19d592-4bb03a7b-65f06402-ae2b8ab1-6b33c7dc", 
       "type": "osimis-viewer-publication", 
       "expiration_date": null}'
```
- then open the url from the response ([sample](http://localhost/shares/osimis-viewer/app/index.html?study=ba19d592-4bb03a7b-65f06402-ae2b8ab1-6b33c7dc&token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6ImRlbW8tMSIsImRpY29tX3VpZCI6IjEuMi4yNzYuMC43MjMwMDEwLjMuMS4yLjIzNDQzMTM3NzUuMTQ5OTIuMTQ1ODA1ODM1OS42ODExIiwib3J0aGFuY19pZCI6ImJhMTlkNTkyLTRiYjAzYTdiLTY1ZjA2NDAyLWFlMmI4YWIxLTZiMzNjN2RjIiwidHlwZSI6Im9zaW1pcy12aWV3ZXItcHVibGljYXRpb24iLCJleHBpcmF0aW9uX2RhdGUiOm51bGx9.JyguRcZmjzU5cvuLXx44dlw3TDCKU1UNXaWPt9fzAIU)). 
- create an anonymized public share by issuing this command:
```bash
curl -X PUT http://localhost:8001/shares -H 'Content-Type: application/json' \
  -d '{"id": "demo-1", 
       "dicom-uid": "1.2.276.0.7230010.3.1.2.2344313775.14992.1458058359.6811", 
       "orthanc-id": "ba19d592-4bb03a7b-65f06402-ae2b8ab1-6b33c7dc", 
       "type": "osimis-viewer-publication", 
       "expiration_date": null}'
```
- then open the url from the response ([sample](http://localhost/anon-shares/osimis-viewer/app/index.html?study=ba19d592-4bb03a7b-65f06402-ae2b8ab1-6b33c7dc&token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6ImRlbW8tMSIsImRpY29tX3VpZCI6IjEuMi4yNzYuMC43MjMwMDEwLjMuMS4yLjIzNDQzMTM3NzUuMTQ5OTIuMTQ1ODA1ODM1OS42ODExIiwib3J0aGFuY19pZCI6ImJhMTlkNTkyLTRiYjAzYTdiLTY1ZjA2NDAyLWFlMmI4YWIxLTZiMzNjN2RjIiwidHlwZSI6Im9zaW1pcy12aWV3ZXItcHVibGljYXRpb24iLCJleHBpcmF0aW9uX2RhdGUiOm51bGx9.JyguRcZmjzU5cvuLXx44dlw3TDCKU1UNXaWPt9fzAIU)). 
