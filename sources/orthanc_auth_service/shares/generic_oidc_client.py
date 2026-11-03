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
from .utils.utils import get_secret_or_die, is_secret_defined, get_json_entry_from_path


# only asymmetric algorithms: HS* and 'none' must never be accepted from an external identity provider
ASYMMETRIC_ALGORITHMS = ["RS256", "RS384", "RS512", "PS256", "PS384", "PS512", "ES256", "ES384", "ES512", "EdDSA"]

class GenericOidcClient:

    def __init__(self, jwks_client: jwt.jwks_client.PyJWKClient, roles_path_in_token: str, issuer: str, audience: str, roles_configuration: RolesConfiguration, jwt_leeway_seconds: int = 0):
        self.jwks_client = jwks_client
        self.issuer = issuer
        self.audience = audience
        self.roles_configuration = roles_configuration
        self.roles_path_in_token = roles_path_in_token
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
            signing_key = self.jwks_client.get_signing_key_from_jwt(jwt_token)
            return jwt.decode(jwt=jwt_token, key=signing_key.key, audience=self.audience, issuer=self.issuer, algorithms=ASYMMETRIC_ALGORITHMS,
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
        Here is a Keyclock token sample:

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
        roles = get_json_entry_from_path(decoded_token, self.roles_path_in_token, None)
        return roles or []

    def get_user_profile_from_token(self, jwt_token: str) -> UserProfileResponse:
        decoded_token = self.decode_token(jwt_token=jwt_token)
        logging.debug(f"decoded_token: {decoded_token}")

        # note: - Keycloak does not fill 'groups' by default unless you have defined a mapping in 'orthanc client' -> client scopes -> orthanc-dedicated mapper.
        #       - Authentic tokens always have 'groups'.  There are equivalent to the realm_access.roles in Keycloak.
        #       - As of Nov 2026, profile->groups are only used in OE2 inbox (FormFields -> UserGroupsChoice)
        groups = None
        if 'groups' in decoded_token:
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


def create_oidc_client_from_secrets(oidc_configuration_url: str, roles_path_in_token: str, audience: str, issuer: Optional[str], roles_configuration: RolesConfiguration, jwt_leeway_seconds: int = 0):

    try:
        response = requests.get(oidc_configuration_url, timeout=10)
        response.raise_for_status()
        configuration = response.json()
        issuer = issuer or configuration["issuer"]
        jwks_client = jwt.PyJWKClient(configuration["jwks_uri"])
        logging.info(f"Got the OIDC configuration for Keycloak, issuer = {issuer}.")

    except Exception as ex:
        logging.exception(ex)
        logging.error(f"Unable to reach the Keycloak - OIDC provider at {oidc_configuration_url}, (be patient, Keycloak may need more than 1 min to start), exiting...")
        exit(-1)

    return GenericOidcClient(jwks_client=jwks_client, roles_path_in_token=roles_path_in_token, issuer=issuer, audience=audience, roles_configuration=roles_configuration, jwt_leeway_seconds=jwt_leeway_seconds)
