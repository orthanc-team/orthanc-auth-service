# SPDX-FileCopyrightText: 2022 - 2024 Orthanc Team SRL <info@orthanc.team>
#
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import logging
import datetime
import requests
import jwt
import jsonc
from typing import Dict, Any, List, Tuple
from .models import *
from .utils.utils import get_secret_or_die, is_secret_defined
from .roles_configuration import RolesConfiguration
import requests
from urllib.parse import urljoin


class KeycloakAdmin:

    def __init__(self, keycloak_uri: str, keycloak_admin_uri: str, keycloak_client_secret: str, roles_configuration: RolesConfiguration):
        self._keycloak_uri = keycloak_uri
        self._keycloak_admin_uri = keycloak_admin_uri
        self._keycloak_client_secret = keycloak_client_secret
        self._roles_configuration = roles_configuration

    def _get_keycloak_access_token(self) -> str:
        keycloak_url = urljoin(self._keycloak_uri, "protocol/openid-connect/token")

        data = {
            'client_id': 'admin-cli',
            'client_secret': self._keycloak_client_secret,
            'grant_type': 'client_credentials'
        }

        response = requests.post(keycloak_url, data=data)
        access_token = response.json()['access_token']
        return access_token

    def get_user_profile_from_api_key(self, api_key: str) -> Optional[UserProfileResponse]:
        keycloak_users_url = urljoin(self._keycloak_admin_uri, f"users?q=api-key:{api_key}")
        headers = {
            'Authorization': 'Bearer ' + self._get_keycloak_access_token(),
            'Content-Type': 'application/json'
        }

        keycloak_user_response = requests.get(keycloak_users_url, headers=headers)

        if keycloak_user_response.status_code == 200:
            users = keycloak_user_response.json()
            if len(users) > 1:
                logging.error("Multiple users found with the same api-key")
                return None
            elif len(users) == 0:
                return None
            else:
                user = users[0]
                if not user['enabled']:
                    logging.error("User is disabled")
                    return None
                if datetime.now() < datetime.utcfromtimestamp(user['notBefore']):
                    logging.error("User is not yet valid")
                    return None

                # retrieve the roles for this user
                keycloak_role_url = urljoin(self._keycloak_admin_uri, f"users/{user['id']}/role-mappings")
                keycloak_role_response = requests.get(keycloak_role_url, headers=headers)
                if keycloak_role_response.status_code != 200:
                    logging.error("Unable to retrieve roles for user")
                    return None

                # keep only the roles that we have defined ourselves
                user_roles = []
                resp_roles = keycloak_role_response.json()
                for resp_role in resp_roles['realmMappings']:
                    if resp_role['name'] in self._roles_configuration.get_all_roles():
                        user_roles.append(resp_role['name'])

                profile_from_config = self._roles_configuration.get_role_configuration(user_roles)

                return UserProfileResponse(
                    name=user['username'],
                    permissions=profile_from_config.permissions,
                    validity=60,
                    authorized_labels=profile_from_config.authorized_labels
                )
        else:
            logging.error("Failed to fetch/search users from api-key from keycloak: " + str(keycloak_user_response.status_code))
            return None

    def get_all_roles(self) -> List[str]:
        try:
            # validate that we can connect to keycloak and retrieve users list
            keycloak_users_url = urljoin(self._keycloak_admin_uri, "roles")
            headers = {
                'Authorization': 'Bearer ' + self._get_keycloak_access_token(),
                'Content-Type': 'application/json'
            }

            response = requests.get(keycloak_users_url, headers=headers)
            if response.status_code != 200:
                logging.error(f"Unable to retrieve roles list from keycloak " + str(response) + ", exiting...")
                exit(-1)

            # avoid the 3 default roles that we won't use
            return [x['name'] for x in response.json() if not x['composite'] and x['name'] not in ['uma_authorization', 'offline_access']]

        except Exception as ex:
            logging.exception(ex)
            logging.error(f"Unable to validate client connection with keycloak, exiting...")
            exit(-1)

    def update_roles_configuration(self, roles_configuration: RolesConfiguration):
        self._roles_configuration = roles_configuration


    # def get_all_roles(self) -> List[str]:

# def create_api_keys(keycloak_uri: str, keycloak_admin_uri: str, keycloak_client_secret: str, roles_configuration: RolesConfiguration):
#     try:
#         #validate that we can connect to keycloak and retrieve users list
#         keycloak_users_url = urljoin(keycloak_admin_uri, "users")
#         headers = {
#             'Authorization': 'Bearer ' + _get_keycloak_access_token(keycloak_uri, keycloak_client_secret),
#             'Content-Type': 'application/json'
#         }
#         response = requests.get(keycloak_users_url, headers=headers)
#         if response.status_code != 200:
#             logging.error(f"Unable to retrieve users list from keycloak to validate client connection " + str(response) + ", exiting...")
#             exit(-1)
#
#         return KeycloakAdmin(keycloak_uri=keycloak_uri,
#                              keycloak_admin_uri=keycloak_admin_uri,
#                              keycloak_client_secret=keycloak_client_secret,
#                              roles_configuration=roles_configuration)
#
#     except Exception as ex:
#         logging.exception(ex)
#         logging.error(f"Unable to validate client connection with keycloak, exiting...")
#         exit(-1)
#
