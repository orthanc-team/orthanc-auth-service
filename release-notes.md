<!--
SPDX-FileCopyrightText: 2022 - 2025 Orthanc Team SRL <info@orthanc.team>

SPDX-License-Identifier: GPL-3.0-or-later
-->

Pending changes
===============

- In `orthanc-auth-service`: 
  - Added new routes to send emails and provide email templates
  - Updated python to 3.14 and updated all python modules
- The minimal keycloak setup now features a mock STMP server.



v 25.12.0
========
- In `orthanc-nginx`: fixed the default value of ENABLE_ORTHANC that is now set to `true`.
- Modified Nginx docker images to avoid the buffering of requests body (removed rewrite directive).
- Added `worklists` in the `UserPermissions` model

v 25.9.0
========
- Update cache cleaner values for the Meddream viewer (according to Softneta recommendations)
- Modified Nginx configuration to fix CVE-2000-0649 (Prevent internal IP disclosure)


v 25.8.1
========

- The nginx reverse proxies now sets all `port`, `host` and `scheme` values in the `Forwarded` HTTP header and in the 
  `X-Forwarded-for/proto/host` headers.  Note that, for the orthanc reverse proxy, only the `Forwarded` header is set
  while for other reverse proxies, all `X-Forwarded-*` headers and the `Forwarded` header are set.
- Updated the `default-app-config.js` in the ohif image since we don't need the `BulkDataURI` configuration anymore.


v 25.8.0
========
- The auth-service can now return `groups` in the User Profile if Keycloack provides the field.
- The auth-service now returns `user-id` in the User Profile.
- The `/user/get-profile` route can now return a basic User Profile with mainly the `name` when requested against a `user-id`.
- upgraded OHIF from v3.10.4 to v3.11.0


v 25.7.0
========
- `orthanc-nginx-certbot` Docker image: upgrade base image (`jonasal/nginx-certbot`) from `5.4.1` to `6.0.0`.
  Behind the scene, this is an upgrade of Certbot from `2.11.0` to `4.1.1`.
- upgraded OHIF from v3.9.2 to v3.10.4


v 25.6.0
========

- New "ANONYMOUS_PROFILE_FILE_PATH" to define the anonymous profile (name & permissions).
- Auth-service now returns a new field `resources` in the `/tokens/decode` route.
  This is required for the last changes of the authorization plugin (v 0.9.3)


v 25.5.0
========

- Nginx Docker image: bugfix: restored / route for http configurations

v 25.3.0
========

BREAKING CHANGE:
- Nginx(-Cerbot) Docker image: replaced `ENABLE_CLIENT_CERTIFICATE_VERIFICATION` by `ENABLE_CLIENT_CERTIFICATE`
  `/orthanc-cert` is now the only route protected by a client cert.


v 25.2.1
========

- Added support for `volview-viewer-publication`.


v 25.2.0
========

- Upgraded Nginx to `1.27.4` and Nginx-Certbot to `5.4.1` (support of Infomaniak DNS-01 Certbot authenticator)
- Added `ENABLE_CLIENT_CERTIFICATE_VERIFICATION` to Nginx and Nginx-Cerbot Docker images.


v 25.1.0
========

- Updated OHIF image with new default value for `bulkDataUri` to fix loading of PDF (https://github.com/OHIF/Viewers/issues/4256)


v 24.12.1
========

- Enabled Keycloak Health probe


v 24.12.0
========

- Upgraded OHIF from v3.9.0-beta.56 to v3.9.2
- Upgraded Keycloak from 25.0.5 to 26.0.7

BREAKING CHANGES:
- Keycloak Docker image env var `KEYCLOAK_ADMIN` is replaced by `KC_BOOTSTRAP_ADMIN_USERNAME`
- Keycloak Docker image env var `KEYCLOAK_ADMIN_PASSWORD` is replace by `KC_BOOTSTRAP_ADMIN_PASSWORD`


v 24.11.0
========

- Improved Keycloak image to automate its initial configuration.


v 24.9.1
========

- Fixed roles removed from Keycloak that were still being listed in `/settings/roles`


v 24.9.0
========

- Fixed typo in `KEYCLOAK_ADMIN_URI` that was not read correctly.
- Fixed special characters that were not allowed in API keys.
- Upgraded Keycloak from 22.0.5 to 25.0.5
- enabled brut force detection by default in orthanc Keycloak realm

BREAKING CHANGES:
- Keycloak Docker image env var `KC_HOSTNAME_URL` is replaced by `KC_HOSTNAME`
- Keycloak Docker image env var `KC_HOSTNAME_ADMIN_URL` is removed (no longer needed)


v 24.7.2
========

- added `PROXY_READ_TIMEOUT` env var for nginx
- fix: read KEYCLOAK_CLIENT_SECRET from secrets or environment variable


v 24.7.1
========

- when requesting a user-profile with e.g. a basic auth token, the auth-service now
  returns the Anonymous profile instead of a 400 such that the auth-plugin can cache
  the response.
- added a new route `/settings/roles` (GET/PUT) in the auth-service to allow reading/editing
  the permissions and authorized-labels for each role.  Also introduced a new `available-labels`
  field in the permission.json.
- Upgraded OHIF from v3.7.0 to v3.9.0-beta.50 to hopefully fix PDF
- Remove "Bearer" prefix from token when decoding user profile if present.
- Added a new Nginx Docker image including Certbot


v 24.5.1
========

- Upgraded OHIF from v3.7.0 to v3.8.0
- in OHIF default configuration, show the "investigational use" warning every 180 days.
- Upgraded Meddream from v8.3.0 to v8.4.0
- demo setups now use "ReadCommitted" Transaction mode


v 24.2.0
========

- added support for Api-keys that can be defined as user custom attributes `api-key`
  in Keycloak.  This requires the definition of 3 new env vars: `ENABLE_KEYCLOAK_API_KEYS`,
  `KEYCLOAK_CLIENT_SECRET` and `KECLOAK_ADMIN_URI`.  This also requires you to configure
  the `admin-cli` client in Keycloak and add `api-key` in the `TokenHttpHeaders` Orthanc Authorization plugin configuration.
  Check the readme.md from the minimal-setup/keycloak sample.


v 24.1.1
========

- made the basic auth mandatory for the auth service


v 24.1.0
========

- modified Meddream Docker image to allow DICOMweb for the connection with Orthanc


v 23.12.2
========

- updated the default OHIF configuration in the ohif image.

v 23.12.1
========
- added DOCUMENT_VIEW in meddream params, so that SR are viewable

v 23.12.0
========

- Modified Nginx docker image to redirect http trafic to https (in case of https configuration)


v 23.11.3
========

- Modified Nginx docker image to handle headers correctly when the Nginx container is behind another Nginx


v 23.11.2
========

- Upgraded Keycloak from 22.0.3 to 22.0.5
- Removed Keycloak plugin to bypass 2FA based on the client ip


v 23.11.1
========

- Upgraded Keycloak from 21.0.1 to 22.0.3
- Added Keycloak plugin to bypass 2FA based on the client ip


v 23.11.0
========

- Upgraded OHIF from v3.6.0 to v3.7.0
- Upgraded Meddream from v8.1.0 to v8.3.0
- Upgraded Meddream token service from 1.3.7 to 2.1.3


v 23.9.0
========
BREAKING CHANGES:
- the format of the permissions.json file has changed to include `permissions` and `authorized_labels`.

- added support of labels permissions (via `authorized_labels` in user roles and user profiles)

BREAKING CHANGES:
- the format of the permissions.json file has changed to include `permissions` and `authorized_labels`.

- nginx: added proxy parameters to handle large headers
- added `OHIF_DATA_SOURCE` env var defaulting to `dicom-web`

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

