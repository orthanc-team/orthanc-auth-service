import logging
import jsonc
import os
from .models import *
from typing import Dict, Any, List, Tuple


def _get_config_from_file(file_path: str):
    with open(file_path) as f:
        data = jsonc.load(f)

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


class RolesConfiguration:

    def __init__(self, roles: Dict[str, Any]):
        self.configured_roles = roles

    def get_roles(self) -> List[str]:
        return self.configured_roles.keys()

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

def create_roles_configuration_from_file(permissions_file_path: str):
    try:
        roles = _get_config_from_file(permissions_file_path)
        logging.info(f"Got the roles and permissions from configuration file")

    except Exception as ex:
        logging.exception(ex)
        logging.error(f"Unable to get roles and permissions from configuration file ({permissions_file_path}), exiting...")
        exit(-1)

    return RolesConfiguration(roles)