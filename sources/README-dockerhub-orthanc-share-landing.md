<!--
SPDX-FileCopyrightText: 2022 Orthanc Team SRL <info@orthanc.team>

SPDX-License-Identifier: CC0-1.0
-->

# Orthanc-share-landing

Web service to run next to Orthanc to handle sharing of studies.
This webservice redirects to the Viewer or displays an error message if the token is not valid.


| Environment variable (to define error messages) | Description                                                                 | default                   |
|-------------------------------------------------|:----------------------------------------------------------------------------|:--------------------------|
| TITLE_EXPIRED_TOKEN                             | Title of the HTML page displayed when the token has expired                 | `Expired Token`           |
| MESSAGE_EXIRED_TOKEN                            | Message displayed when the token has expired.  This may contain html tags. | `Your token has expired.<br/>You should ask for a new one.` |
| TITLE_INVALID_TOKEN                             | Title of the HTML page displayed when the token is invalid                  | `Invalid Token`           |
| MESSAGE_INVALID_TOKEN                           | Message displayed when the token is invalid.  This may contain html tags.                                 | `Your token is invalid.<br/>Please check that you have copied it entirely.`  |

Note that if you want to fully customize the error message, you may also provide these files in the image:
- `/orthanc-share/landing-pages/expired-token.html`
- `/orthanc-share/landing-pages/invalid-token.html`

Full documentation and demo setup will be available [here](https://github.com/orthanc-team/orthanc-share/tree/main).
