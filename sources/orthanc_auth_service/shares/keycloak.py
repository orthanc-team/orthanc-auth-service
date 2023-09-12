# SPDX-FileCopyrightText: 2022 - 2023 Orthanc Team SRL <info@orthanc.team>
#
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import logging
import requests
import jwt
import json
from typing import Dict, Any, List, Tuple
from .models import *
from .utils.utils import get_secret_or_die, is_secret_defined


class Keycloak:

    def __init__(self, public_key, configured_roles: Dict[str, Any]):
        self.public_key = public_key
        self.configured_roles = configured_roles

    def decode_token(self, jwt_token: str) -> Dict[str, Any]:
        return jwt.decode(jwt=jwt_token, key=self.public_key, audience="account", algorithms=["RS256"])

    def get_name_from_decoded_token(self, decoded_token: Dict[str, Any]) -> str:
        name = decoded_token.get('name')
        if name is not None:
            return name
        return ''

    def get_roles_from_decoded_token(self, decoded_token: Dict[str, Any]) -> List[str]:
        '''
        Returns the roles extracted form the token.
        Here is token sample:

            {
            "exp": 1676637999,
            "iat": 1676637699,
            "auth_time": 1676626268,
            "jti": "2443e1e4-74cc-4eae-bc1b-cec65a7b401c",
            "iss": "http://localhost:8080/realms/orthanc-realm",
            "aud": "account",
            "sub": "3cd50e87-a0e6-40a4-bebf-3eab0cb7b6c0",
            "typ": "Bearer",
            "azp": "orthanc-id",
            "nonce": "c5a6737c-70ea-4703-85e3-bf660c473fae",
            "session_state": "5b0cdfa4-0781-4b69-a0e9-171ff5d4ded3",
            "acr": "0",
            "allowed-origins": [
                "*"
            ],
            "realm_access": {
                "roles": [
                "default-roles-orthanc-realm",
                "offline_access",
                "uma_authorization",
                "orthanc-admin"
                ]
            },
            "resource_access": {
                "account": {
                "roles": [
                    "manage-account",
                    "manage-account-links",
                    "view-profile"
                ]
                }
            },
            "scope": "openid profile email",
            "sid": "5b0cdfa4-0781-4b69-a0e9-171ff5d4ded3",
            "email_verified": false,
            "name": "my user",
            "preferred_username": "myuser",
            "given_name": "my",
            "family_name": "user"
            }

        '''
        realm_access = decoded_token.get('realm_access')
        if realm_access is not None:
            roles = realm_access.get('roles')
            if roles is not None:
                return roles
        return []

    def get_user_profile_from_token(self, jwt_token: str) -> UserProfileResponse:
        decoded_token = self.decode_token(jwt_token=jwt_token)
        response = UserProfileResponse(name="", permissions=[], validity=60, authorized_labels=[])

        response.name = self.get_name_from_decoded_token(decoded_token=decoded_token)

        roles = self.get_roles_from_decoded_token(decoded_token=decoded_token)

        response.permissions, response.authorized_labels = self.get_role_configuration(roles)

        return response


    def get_role_configuration(self, roles: List[str]) -> Tuple[List[UserPermissions], List[str], List[str]]:
        permissions = []
        authorized_labels = []
        configured_user_roles = []

        for r in roles:
            if r in self.configured_roles:
                configured_user_roles.append(r)

        # complain if there are 2 roles for the same user ???  How should we combine the authorized and forbidden labels in this case ???
        if len(configured_user_roles) > 1:
            raise ValueError("Unable to handle multiple roles for a single user")

        role = configured_user_roles[0]
        # search for it in the configured roles
        configured_role = self.configured_roles.get(role)
        # if it has been configured:
        if configured_role is None:
            raise ValueError(f"Role not found in configuration: {role}")

        for item in configured_role.get('permissions'):
            # (if not already there)
            if UserPermissions(item) not in permissions:
                permissions.append(UserPermissions(item))

        if configured_role.get("authorized_labels"):
            authorized_labels = configured_role.get("authorized_labels")

        return permissions, authorized_labels


def _get_keycloak_public_key(keycloak_uri: str) -> str:
    '''
    - get public key from keycloak server
    - add "-----BEGIN PUBLIC KEY-----" (and same for the end)
    - return it as a bytes string
    '''

    public_key = requests.get(keycloak_uri).json().get("public_key")

    begin_public_key = "-----BEGIN PUBLIC KEY-----\n"
    end_public_key = "\n-----END PUBLIC KEY-----"

    return ''.join([begin_public_key, public_key, end_public_key]).encode()


def _get_config_from_file(file_path: str):
    with open(file_path) as f:
        data = json.load(f)

    roles = data.get('roles')

    for key, role_def in roles.items():
        if not role_def.get("authorized_labels"):
            msg = f'No "authorized_labels" defined for role "{key}".  You should, e.g,  include "authorized_labels" = ["*"] if you want to authorize all labels.")'
            logging.error(msg)
            raise ValueError(msg)

        if not role_def.get("permissions"):
            msg = f'No "permissions" defined for role "{key}".  You should, e.g,  include "permissions" = ["all"] if you want to authorize all permissions.")'
            logging.error(msg)
            raise ValueError(msg)

    return roles


def create_keycloak_from_secrets():
    handle_users_with_keycloak = os.environ.get("ENABLE_KEYCLOAK", "false") == "true"

    if not handle_users_with_keycloak:
        logging.warning("ENABLE_KEYCLOAK is not set, won't use keycloak and will not handle users")
        return None

    logging.warning("ENABLE_KEYCLOAK is set, will handle users with Keycloak")
    keycloak_uri = os.environ.get("KEYCLOAK_URI", "http://keycloak:8080/realms/orthanc/")
    permissions_file_path = os.environ.get("PERMISSIONS_FILE_PATH", "/orthanc_auth_service/permissions.json")

    try:
        public_key = _get_keycloak_public_key(keycloak_uri)
        logging.info(f"Got the public key from Keycloak.")

    except Exception as ex:
        logging.exception(ex)
        logging.error(f"Unable to reach keycloak (be patient, Keycloak may need more than 1 min to start), exiting...")
        exit(-1)

    try:
        configured_roles = _get_config_from_file(permissions_file_path)
        logging.info(f"Got the roles and permissions from configuration file")

    except Exception as ex:
        logging.exception(ex)
        logging.error(f"Unable to get roles and permissions from configuration file ({permissions_file_path}), exiting...")
        exit(-1)

    return Keycloak(public_key=public_key, configured_roles=configured_roles)
