# SPDX-FileCopyrightText: 2022 - 2026 Orthanc Team SRL <info@orthanc.team>
#
# SPDX-License-Identifier: GPL-3.0-or-later

import base64
import hashlib
import hmac
import json
import time
import pathlib
import unittest
from unittest import mock
from types import SimpleNamespace

import jwt
import requests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from orthanc_auth_service.shares.oidc import OidcClient, create_oidc_from_secrets
from orthanc_auth_service.shares.keycloak import Keycloak
from orthanc_auth_service.shares.roles_configuration import RolesConfiguration

here = pathlib.Path(__file__).parent.resolve()
permissions_file = str(here.parent / "orthanc_auth_service" / "permissions.json")

private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
public_key = private_key.public_key()
public_pem = public_key.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)


class FakeJwksClient:
    def __init__(self, key):
        self.key = key

    def get_signing_key_from_jwt(self, token):
        return SimpleNamespace(key=self.key)


def make_token(claims, alg="RS256", key=private_key, headers={"kid": "k1"}):
    return jwt.encode(claims, key, algorithm=alg, headers=headers)


def base_claims(**overrides):
    claims = {
        "iss": "https://idp/application/o/orthanc/",
        "aud": "orthanc",
        "sub": "u1",
        "exp": int(time.time()) + 300,
        "preferred_username": "alice",
        "groups": ["admin-role"],
    }
    claims.update(overrides)
    return {k: v for k, v in claims.items() if v is not None}


class TestOidcClient(unittest.TestCase):

    def make_client(self, jwks_client=None, jwt_leeway_seconds=0):
        return OidcClient(
            jwks_client=jwks_client or FakeJwksClient(public_key),
            issuer="https://idp/application/o/orthanc/",
            audience="orthanc",
            roles_configuration=RolesConfiguration(permissions_file_path=permissions_file, anonymous_profile_file_path=None),
            jwt_leeway_seconds=jwt_leeway_seconds)

    def test_valid_token_permissions_from_groups(self):
        profile = self.make_client().get_user_profile_from_token(make_token(base_claims()))
        self.assertEqual("alice", profile.name)
        self.assertEqual("u1", profile.user_id)
        self.assertIn("view", profile.permissions)
        self.assertEqual(["*"], profile.authorized_labels)

    def test_missing_groups_claim(self):
        profile = self.make_client().get_user_profile_from_token(make_token(base_claims(groups=None)))
        self.assertEqual([], profile.permissions)

    def test_wrong_audience(self):
        with self.assertRaises(jwt.InvalidAudienceError):
            self.make_client().decode_token(make_token(base_claims(aud="other")))

    def test_wrong_issuer(self):
        with self.assertRaises(jwt.InvalidIssuerError):
            self.make_client().decode_token(make_token(base_claims(iss="https://evil/")))

    def test_expired_token(self):
        with self.assertRaises(jwt.ExpiredSignatureError):
            self.make_client().decode_token(make_token(base_claims(exp=int(time.time()) - 3600)))

    def test_leeway_accepts_slightly_expired(self):
        client = self.make_client(jwt_leeway_seconds=10)
        claims = client.decode_token(make_token(base_claims(exp=int(time.time()) - 5)))
        self.assertEqual("u1", claims["sub"])

    def test_hs256_token_rejected(self):
        # built by hand with a non-PEM secret: PyJWT refuses HMAC with a PEM key, which would mask an allowed HS256
        secret = b"shared-secret-shared-secret-32by"
        def b64(data):
            return base64.urlsafe_b64encode(data).rstrip(b"=")
        signing_input = b64(json.dumps({"alg": "HS256", "kid": "k1"}).encode()) + b"." + b64(json.dumps(base_claims()).encode())
        signature = hmac.new(secret, signing_input, hashlib.sha256).digest()
        token = (signing_input + b"." + b64(signature)).decode()
        client = self.make_client(jwks_client=FakeJwksClient(secret))
        with self.assertRaises(jwt.InvalidAlgorithmError):
            client.decode_token(token)

    def test_keycloak_mode_unchanged(self):
        keycloak = Keycloak(
            public_key=public_pem,
            roles_configuration=RolesConfiguration(permissions_file_path=permissions_file, anonymous_profile_file_path=None))
        token = make_token({"aud": "account", "sub": "u1", "exp": int(time.time()) + 300,
                            "realm_access": {"roles": ["admin-role"]}})
        self.assertIn("view", keycloak.get_user_profile_from_token(token).permissions)


class TestOidcFactory(unittest.TestCase):
    discovery = {"issuer": "https://idp/application/o/orthanc/", "jwks_uri": "https://idp/application/o/orthanc/jwks/"}

    def create(self, issuer):
        with mock.patch("requests.get") as get:
            get.return_value.json.return_value = self.discovery
            return create_oidc_from_secrets(
                configuration_url="https://idp/.well-known/openid-configuration", audience="orthanc", issuer=issuer,
                roles_configuration=RolesConfiguration(permissions_file_path=permissions_file, anonymous_profile_file_path=None))

    def test_factory_uses_discovery_issuer(self):
        client = self.create(issuer=None)
        self.assertEqual("https://idp/application/o/orthanc/", client.issuer)
        self.assertEqual("https://idp/application/o/orthanc/jwks/", client.jwks_client.uri)

    def test_issuer_override_used_verbatim(self):
        client = self.create(issuer="https://idp/application/o/orthanc")
        self.assertEqual("https://idp/application/o/orthanc", client.issuer)
        client.jwks_client = FakeJwksClient(public_key)
        with self.assertRaises(jwt.InvalidIssuerError):
            client.decode_token(make_token(base_claims()))

    def test_factory_exits_when_unreachable(self):
        with mock.patch("requests.get", side_effect=requests.ConnectionError):
            with self.assertRaises(SystemExit):
                create_oidc_from_secrets(
                    configuration_url="https://idp/.well-known/openid-configuration", audience="orthanc", issuer=None, roles_configuration=None)


if __name__ == '__main__':
    unittest.main()
