<!--
SPDX-FileCopyrightText: 2022 - 2023 Orthanc Team SRL <info@orthanc.team>

SPDX-License-Identifier: GPL-3.0-or-later
-->

v x.x.x
========

- nginx: added proxy parameters to handle large headers


v 23.6.1
========

- new user permission: `edit-labels`
- updated OHIF to v3.6.0

v 23.6.0
========

- bug fix: changed the `large_client_header_buffers` value in nginx to avoid http error 414 (`Request-URI Too Large`) when a huge number of studies are loaded in the viewer
- enhancement: added Meddream default values for the Meddream viewer to manage the clean up of the cache

v 23.5.0
========

- support for `ohif-viewer-publication`
- now building `orthancteam:ohif-v3` docker image


v 23.4.0
========
- nginx config: added a redirect in the orthanc.conf to get the app easily reachable (`http://localhost/` in place of `http://localhost/orthanc/ui/app/`)
- upgraded Meddream base image from 8.0.0 to 8.1.0
- upgraded Meddream token service base image from 


v 23.3.0
========

- almost completely rewrote the project.  Make sure to read the documentation and check the minimal setups again.
- repository renamed from `orthanc-share` to `orthanc-auth-service`
- replaced orthanc-for-ingest by orthanc-for-api

v 23.1.0
========

- added permissions stuff in meddream prop file to enable Export button when the viewer is opened through a token

v 22.11.4
========

- added admin user (and corresponding env var) to meddream properties file, so that, registration page is reachable to fill a licence key

v 22.11.3
========

- fix support for `stone-viewer-publication`
- demo-setup: simplified authorization plugin configuration (v0.4.0)

v 22.11.2
========

- `orthanc-share-landing`: added 4 env var to customize error messages + ability to provide your own html files for error messages.

v 22.11.1
========

- added support for `stone-viewer-publication` but not yet functional, need an updated orthanc-authorization plugin
- added new `ENABLE_HTTPS` env var in `orthanc-nginx` docker image.

v 22.11.0
========

- fix sharing studies with Osimis viewer (take into account multiple studies API) 

v 22.10.7
========

- fix `orthanc-ingest`

v 22.10.6
========

- BREAKING-CHANGE: `orthanc-token-service` API: `study` field has been renamed into `studies` and is now a list of `SharedStudy`.

v 22.10.5
========

- new `ENABLE_ORTHANC_FOR_INGEST` env var in `orthanc-nginx` docker image.

v 22.10.4
========

- BREAKING-CHANGE: in Rest API: renamed `expiration_date` into `expiration-date`

v 22.10.3
========

- Fixed token verification if one of the id is `null`
- improvied logging in case of id mismatch

v 22.10.2
========

- Added `USERS` env var for `orthanc-tokenc-service` to list the allowed users login/pwd
- Added the `orthanc-nginx` Docker image.

v 22.10.1
========

- Made `id` parameter optional for share request

v 22.9.0
========

- Full refactoring of the code
- introduced server-identifier (auth plugin v 0.3.0)
- allow MedDream shares + anonymized shares
- now generating 5 Docker images
  - `orthancteam:orthanc-token-service`
  - `orthancteam:orthanc-share-landing`
  - `orthancteam:orthanc-anonymizer`
  - `orthancteam:meddream-viewer`
  - `orthancteam:meddream-token-service`

