# SPDX-FileCopyrightText: 2022 - 2023 Orthanc Team SRL <info@orthanc.team>
#
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import logging
import requests
import jwt
import jsonc
from typing import Dict, Any, List, Tuple
from .models import *
from .utils.utils import get_secret_or_die, is_secret_defined
from .roles_configuration import RolesConfiguration

class ApiKeys:

    def __init__(self, role_per_key: Dict[str, str], roles_configuration: RolesConfiguration):
        self.role_per_key = role_per_key
        self.roles_configuration = roles_configuration

    def get_role_from_api_key(self, api_key: str) -> List[str]:
        if api_key in self.role_per_key:
            return self.role_per_key[api_key]
        else:
            logging.warning(f"No role found for api-key")
            return None


    def get_user_profile_from_api_key(self, api_key: str) -> UserProfileResponse:
        response = UserProfileResponse(
            name="API KEY",
            permissions=[],
            validity=60,
            authorized_labels=[])

        role = self.get_role_from_api_key(api_key=api_key)

        response.permissions, response.authorized_labels = self.roles_configuration.get_role_configuration([role])

        return response

def create_api_keys_from_file(api_keys_file_path: str, roles_configuration: RolesConfiguration):
    try:
        with open(api_keys_file_path) as f:
            role_per_key = jsonc.load(f)

        for key, role in role_per_key.items():
            if role not in roles_configuration.get_roles():
                logging.error(f"Unknown role in Api-keys file: {role}")
                exit(-1)

        return ApiKeys(role_per_key=role_per_key, roles_configuration=roles_configuration)

    except Exception as ex:
        logging.exception(ex)
        logging.error(f"Unable to get api-keys from configuration file ({api_keys_file_path}), exiting...")
        exit(-1)

