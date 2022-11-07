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

