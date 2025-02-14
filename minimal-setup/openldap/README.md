# SPDX-FileCopyrightText: 2022 - 2025 Orthanc Team SRL <info@orthanc.team>
#
# SPDX-License-Identifier: CC0-1.0
# What is it about?

This is a tiny setup to quickly spin up an LDAP server to perform some tests (with Keycloak).
All users have the same password:
```
change-me
```

## Cheat code to run it aside Keycloak

From the keycloak folder (minimal-setup):
```
docker compose -f docker-compose.yml -f ../openldap/docker-compose.yml up -d
```

## Login to the mgmt web ui
```
http://localhost:6443

cn=admin,dc=myorg,dc=com
change-me
```

## List all the users from the terminal
``` 
ldapsearch -x -H ldap://localhost:389 -D "cn=admin,dc=myorg,dc=com" -w "change-me"  -b "OU=users,DC=myorg,DC=com"
```