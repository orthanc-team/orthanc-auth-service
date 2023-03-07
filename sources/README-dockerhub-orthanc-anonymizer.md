<!--
SPDX-FileCopyrightText: 2022 - 2023 Orthanc Team SRL <info@orthanc.team>

SPDX-License-Identifier: CC0-1.0
-->

# Orthanc-anonymizer

Web service to run in front of Orthanc to anonymize some of the routes on-the-fly.  
Right now, it only anonymizes routes used by the OsimisViewer in the scope of anonymized publication links.


In order to use this image, you should define these environment variables or Docker secrets:
  - `ORTHANC_ROOT` is the url of the Orthanc that needs to be anonymized

Full sample setup will be available [here](https://github.com/orthanc-team/orthanc-share/tree/main/demo-setup).
