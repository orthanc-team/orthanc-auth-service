# SPDX-FileCopyrightText: 2022 - 2026 Orthanc Team SRL <info@orthanc.team>
#
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
import requests
import jwt
from typing import Dict, Any, List, Optional
from .keycloak import Keycloak
from .roles_configuration import RolesConfiguration

# only asymmetric algorithms: HS* and 'none' must never be accepted from an external identity provider
ASYMMETRIC_ALGORITHMS = ["RS256", "RS384", "RS512", "PS256", "PS384", "PS512", "ES256", "ES384", "ES512", "EdDSA"]


class OidcClient(Keycloak):
    '''
    Validates the tokens of a generic OIDC provider (e.g. Authentik): the signing key is
    selected from the provider's JWKS, the issuer and the audience are verified.
    '''

    def __init__(self, jwks_client, issuer: str, audience: str, roles_configuration: RolesConfiguration, jwt_leeway_seconds: int = 0):
        super().__init__(public_key=None, roles_configuration=roles_configuration, jwt_leeway_seconds=jwt_leeway_seconds)
        self.jwks_client = jwks_client
        self.issuer = issuer
        self.audience = audience

    def _verify_token(self, jwt_token: str) -> Dict[str, Any]:
        signing_key = self.jwks_client.get_signing_key_from_jwt(jwt_token)
        return jwt.decode(jwt=jwt_token, key=signing_key.key, algorithms=ASYMMETRIC_ALGORITHMS,
                          audience=self.audience, issuer=self.issuer, leeway=self.jwt_leeway_seconds)

    def get_roles_from_decoded_token(self, decoded_token: Dict[str, Any]) -> List[str]:
        roles = decoded_token.get('groups')
        return roles if isinstance(roles, list) else []


def create_oidc_from_secrets(configuration_url: str, audience: str, issuer: Optional[str], roles_configuration: RolesConfiguration, jwt_leeway_seconds: int = 0):

    try:
        response = requests.get(configuration_url, timeout=10)
        response.raise_for_status()
        configuration = response.json()
        issuer = issuer or configuration["issuer"]
        jwks_client = jwt.PyJWKClient(configuration["jwks_uri"])
        logging.info(f"Got the OIDC configuration, issuer = {issuer}.")

    except Exception as ex:
        logging.exception(ex)
        logging.error(f"Unable to reach the OIDC provider at {configuration_url}, exiting...")
        exit(-1)

    return OidcClient(jwks_client=jwks_client, issuer=issuer, audience=audience,
                      roles_configuration=roles_configuration, jwt_leeway_seconds=jwt_leeway_seconds)
