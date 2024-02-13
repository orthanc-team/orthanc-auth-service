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

def _get_keycloak_access_token(keycloak_uri: str, keycloak_client_secret: str) -> str:
    keycloak_url =  urljoin(keycloak_uri, "protocol/openid-connect/token")

    data = {
        'client_id': 'admin-cli',
        'client_secret': keycloak_client_secret,
        'grant_type': 'client_credentials'
    }

    response = requests.post(keycloak_url, data=data)
    access_token = response.json()['access_token']
    return access_token

class ApiKeys:

    def __init__(self, keycloak_uri: str, keycloak_admin_uri: str, keycloak_client_secret: str, roles_configuration: RolesConfiguration):
        self.keycloak_uri = keycloak_uri
        self.keycloak_admin_uri = keycloak_admin_uri
        self.keycloak_client_secret = keycloak_client_secret
        self.roles_configuration = roles_configuration

    def get_user_profile_from_api_key(self, api_key: str) -> Optional[UserProfileResponse]:
        keycloak_users_url = urljoin(self.keycloak_admin_uri, f"users?q=api-key:{api_key}")
        headers = {
            'Authorization': 'Bearer ' + _get_keycloak_access_token(self.keycloak_uri, self.keycloak_client_secret),
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
                keycloak_role_url = urljoin(self.keycloak_admin_uri, f"users/{user['id']}/role-mappings")
                keycloak_role_response = requests.get(keycloak_role_url, headers=headers)
                if keycloak_role_response.status_code != 200:
                    logging.error("Unable to retrieve roles for user")
                    return None

                # keep only the roles that we have defined ourselves
                roles = []
                resp_roles = keycloak_role_response.json()
                for resp_role in resp_roles['realmMappings']:
                    if resp_role['name'] in self.roles_configuration.get_roles():
                        roles.append(resp_role['name'])

                response = UserProfileResponse(
                    name=user['username'],
                    permissions=[],  # populated below
                    validity=60,
                    authorized_labels=[] # populated below
                )

                response.permissions, response.authorized_labels = self.roles_configuration.get_role_configuration(roles)

            return response
        else:
            logging.error("Failed to fetch/search users from api-key from keycloak: " + str(keycloak_response))
            return None

def create_api_keys(keycloak_uri: str, keycloak_admin_uri: str, keycloak_client_secret: str, roles_configuration: RolesConfiguration):
    try:
        #validate that we can connect to keycloak and retrieve users list
        keycloak_users_url = urljoin(keycloak_admin_uri, "users")
        headers = {
           'Authorization': 'Bearer ' + _get_keycloak_access_token(keycloak_uri, keycloak_client_secret),
            'Content-Type': 'application/json'
        }
        response = requests.get(keycloak_users_url, headers=headers)
        if response.status_code != 200:
            logging.error(f"Unable to retrieve users list from keycloak to validate client connection " + str(response) + ", exiting...")
            exit(-1)

        return ApiKeys(keycloak_uri=keycloak_uri,
                       keycloak_admin_uri=keycloak_admin_uri,
                       keycloak_client_secret=keycloak_client_secret,
                       roles_configuration=roles_configuration)

    except Exception as ex:
        logging.exception(ex)
        logging.error(f"Unable to validate client connection with keycloak, exiting...")
        exit(-1)

