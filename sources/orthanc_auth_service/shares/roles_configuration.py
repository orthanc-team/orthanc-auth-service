# SPDX-FileCopyrightText: 2022 - 2026 Orthanc Team SRL <info@orthanc.team>
#
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
import jsonc
import os
from .models import *
from typing import Dict, Any, List, Tuple



class RolesConfiguration:

    _configured_roles: RolesConfigurationModel = None
    _anonymous_profile: UserProfileResponse = None
    _permissions_file_path: str = None
    _anonymous_permissions_file_path: str = None

    def __init__(self, permissions_file_path: str, anonymous_profile_file_path: Optional[str]):
        self._permissions_file_path = permissions_file_path
        self._anonymous_profile_file_path = anonymous_profile_file_path
        self._load_roles_configuration_from_file()

    def _load_roles_configuration_from_file(self):
        try:
            with open(self._permissions_file_path) as f:
                data = jsonc.load(f)

            self._configured_roles = RolesConfigurationModel.model_validate(data)
            logging.info(f"Got the roles and permissions from configuration file")

        except Exception as ex:
            logging.exception(ex)
            logging.error(f"Unable to get roles and permissions from configuration file ({self._permissions_file_path}), exiting...")
            exit(-1)

        self._anonymous_profile = UserProfileResponse(
            name="Anonymous",
            user_id=None,
            permissions=[],
            groups=[],
            authorized_labels=[],
            validity=60)

        if self._anonymous_profile_file_path:
            try:
                with open(self._anonymous_profile_file_path) as f:
                    data = jsonc.load(f)

                self._anonymous_profile = UserProfileResponse.model_validate(data)
                logging.info(f"Got the anonymous profile from configuration file")

            except Exception as ex:
                logging.exception(ex)
                logging.error(f"Unable to get anonymous profile from configuration file ({self._anonymous_profile_file_path}), considering anonymous users haven't access to anything")


    def get_anonymous_profile(self):
        return self._anonymous_profile


    def get_configured_roles(self) -> RolesConfigurationModel:
        return self._configured_roles


    def update_configured_roles(self, new_configuration: RolesConfigurationModel):
        self._configured_roles = new_configuration

        logging.warning(f"Writing the new roles and permissions to configuration file ({self._permissions_file_path})")
        with open(self._permissions_file_path, "wt") as f:
            f.write(self._configured_roles.model_dump_json(indent=2, by_alias=True))


    def get_role_configuration(self, user_roles: List[str]) -> RolePermissions:
        configured_user_roles = []

        # discard some of the default roles provided by Keycloak for which we do not have any configurations
        for r in user_roles:
            if r in self._configured_roles.roles:
                configured_user_roles.append(self._configured_roles.roles[r])

        output = RolePermissions()

        for configured_role in configured_user_roles:
            for perm in configured_role.permissions:
                if perm not in output.permissions:
                    output.permissions.append(perm)

            for label in configured_role.authorized_labels:
                if label not in output.authorized_labels:
                    output.authorized_labels.append(label)

        return output


