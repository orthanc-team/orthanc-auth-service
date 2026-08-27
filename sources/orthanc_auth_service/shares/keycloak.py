# SPDX-FileCopyrightText: 2022 - 2026 Orthanc Team SRL <info@orthanc.team>
#
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import time
import logging
import requests
import jwt
import jsonc
from typing import Dict, Any, List, Tuple, Optional
from .models import *
from .roles_configuration import RolesConfiguration
from .utils.utils import get_secret_or_die, is_secret_defined


class Keycloak:

    def __init__(self, public_key, roles_configuration: RolesConfiguration, jwt_leeway_seconds: int = 0):
        self.public_key = public_key
        self.roles_configuration = roles_configuration
        self.jwt_leeway_seconds = jwt_leeway_seconds

    def _get_unverified_claims(self, jwt_token: str) -> Optional[Dict[str, Any]]:
        '''
        Returns the token claims without performing any verification, or None if the token
        is too malformed to be parsed at all.
        Note: verify_signature:False turns off all kinds of claim verifications, not just the 
        cryptographic signature, see https://github.com/jpadilla/pyjwt/blob/2.13.0/jwt/api_jwt.py#L79-L87
        '''
        try:
            return jwt.decode(jwt=jwt_token, options={"verify_signature": False})
        except jwt.PyJWTError:
            return None

    def decode_token(self, jwt_token: str) -> Dict[str, Any]:
        try:
            return jwt.decode(jwt=jwt_token, key=self.public_key, audience="account", algorithms=["RS256"],
                               leeway=self.jwt_leeway_seconds)
        except jwt.PyJWTError as ex:
            # verification failed before we could log the claims -> decode again without
            # verifying so we can see exactly what the token contains. (and compare against
            # this server's clock, since some errors, e.g. ImmatureSignatureError or
            # ExpiredSignatureError, are caused by clock skew between Keycloak and this host)
            unverified_claims = self._get_unverified_claims(jwt_token)

            if unverified_claims is None:
                logging.error(
                    f"PyJWT rejected token ({type(ex).__name__}): {ex}. "
                    f"The token is malformed, its claims cannot be read."
                )
            else:
                logging.error(
                    f"PyJWT rejected token ({type(ex).__name__}): {ex}. "
                    f"This server's current time (utc epoch)={int(time.time())}, "
                    f"token iat={unverified_claims.get('iat')}, exp={unverified_claims.get('exp')}, "
                    f"auth_time={unverified_claims.get('auth_time')}. "
                    f"Full unverified claims: {unverified_claims}"
                )
            raise

    def get_name_from_decoded_token(self, decoded_token: Dict[str, Any]) -> str:
        if decoded_token.get('name'):
            return decoded_token.get('name')

        if decoded_token.get("preferred_username"):
            return decoded_token.get("preferred_username")

        return ''

    def get_id_from_decoded_token(self, decoded_token: Dict[str, Any]) -> str:
        return decoded_token.get('sub')

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
        logging.debug(f"decoded_token: {decoded_token}")
        groups = None
        if 'groups' in decoded_token:  # this might have not been configured in Keycloak (see 'orthanc client' -> client scopes -> orthanc-dedicated mapper)
            groups = decoded_token['groups']
        response = UserProfileResponse(
            name=self.get_name_from_decoded_token(decoded_token=decoded_token),
            user_id=self.get_id_from_decoded_token(decoded_token=decoded_token),
            permissions=[],
            groups=groups,
            validity=60,
            authorized_labels=[])

        roles = self.get_roles_from_decoded_token(decoded_token=decoded_token)
        logging.debug(f"roles: {roles}")

        role_config = self.roles_configuration.get_role_configuration(roles)
        logging.debug(f"role_config: {role_config}")

        response.permissions = role_config.permissions
        response.authorized_labels = role_config.authorized_labels

        logging.debug(f"response (UserProfileResponse object): {response}")

        return response




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




def create_keycloak_from_secrets(keycloak_uri: str, roles_configuration: RolesConfiguration, jwt_leeway_seconds: int = 0):

    try:
        public_key = _get_keycloak_public_key(keycloak_uri)
        logging.info(f"Got the public key from Keycloak.")

    except Exception as ex:
        logging.exception(ex)
        logging.error(f"Unable to reach keycloak (be patient, Keycloak may need more than 1 min to start), exiting...")
        exit(-1)

    return Keycloak(public_key=public_key, roles_configuration=roles_configuration, jwt_leeway_seconds=jwt_leeway_seconds)
