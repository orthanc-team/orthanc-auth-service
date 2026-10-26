<!--
SPDX-FileCopyrightText: 2022 - 2026 Orthanc Team SRL <info@orthanc.team>

SPDX-License-Identifier: CC-BY-4.0
-->

# Purpose

Minimal setup showing how to authenticate Orthanc users with a generic OIDC provider,
[Authentik](https://goauthentik.io/) here, instead of Keycloak.  Roles come from the Authentik groups.

# Description

- `orthanc` + `orthanc-db`: Orthanc with Orthanc Explorer 2 (OE2).
- `orthanc-auth-service`: validates the Authentik tokens and maps groups to the roles of [permissions.jsonc](permissions.jsonc).
- `authentik-server`, `authentik-worker`, `authentik-db`: Authentik.  The OIDC client, the application, the groups
  and the demo users are created at startup by the blueprint [blueprints/orthanc.yaml](blueprints/orthanc.yaml).
- `orthanc-nginx`: reverse proxy.  Authentik is not behind it: it is exposed on its own port 9000.

# Warning

**Disclaimer**: this sample is provided 'as is' without any guarantee.  Don't use it in production unless you perfectly understand every part of it.

Before you use it in production make sure to update all hardcoded passwords and secret keys (search for `change-me`).

# Minimum versions

- `orthancteam/orthanc`: `<next OE2 release>` (first release with `Keycloak.OidcProvider`)
- `orthancteam/orthanc-auth-service`: `<next auth-service release>` (first release with `OIDC_CONFIGURATION_URL`)

# Starting the setup

`docker compose up`.  The first start takes a while: Authentik must migrate its database and apply the blueprint.
`orthanc-auth-service` restarts a few times until Authentik is up (it exits when the discovery URL is unreachable).

# Demo

- Orthanc UI: [http://localhost/orthanc/ui/app/](http://localhost/orthanc/ui/app/)
- Authentik admin: [http://localhost:9000/](http://localhost:9000/) (first start only: set the password of `akadmin`)

Demo logins (for demo only, created by the blueprint, the password is `change-me`):

| user          | group (role)  | rights                                            |
|---------------|---------------|---------------------------------------------------|
| `admin-demo`  | `admin-role`  | everything                                        |
| `doctor-demo` | `doctor-role` | view, download, share, send; no upload/delete     |

# Remote access

Replace `localhost` by your domain in `docker-compose.yml` (`OidcProvider`, `OIDC_ISSUER`, `PUBLIC_*`)
and in the redirect URI pattern (`http://localhost/orthanc/ui/app/.*`: it must start with the scheme, no `^`, and dots must be escaped, e.g. `http://orthanc\.example\.com/orthanc/ui/app/.*`) of [blueprints/orthanc.yaml](blueprints/orthanc.yaml).  `OIDC_ISSUER` must be
exactly the issuer seen by the browser, trailing slash included.

# Known limitations

- No `CheckLoginIframe`: a logout done in another tab is detected only when the access token expires.
- No api-keys and no role edition from the UI (Keycloak only).
- The "change password" button of OE2 is Keycloak only; change passwords in Authentik.
- After logout the user stays on Authentik's "logged out" page: no logout redirect URI is configured, so `post_logout_redirect_uri` is ignored.
- No token refresh (keycloak-js cannot use Authentik's opaque refresh tokens): the OE2 session lasts the access token validity (8 h in this demo), then reload the page.
