# SPDX-FileCopyrightText: 2022 - 2023 Orthanc Team SRL <info@orthanc.team>
#
# SPDX-License-Identifier: GPL-3.0-or-later

from fastapi import FastAPI, Request, status, Header, HTTPException, Depends, Query
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import logging
import json
import secrets
import os
from datetime import timedelta
import requests
import jwt
import pytz
from shares.models import *
from shares.orthanc_token_service_factory import create_token_service_from_secrets


logging.basicConfig(level=logging.DEBUG)

token_service = create_token_service_from_secrets()
app = FastAPI()

# check if the service requires basic auth (by checking of some USERS have been defined)
basic_auth_users = json.loads(os.environ.get("USERS", "null"))
is_basic_auth_enabled = basic_auth_users is not None and len(basic_auth_users) > 0

if is_basic_auth_enabled:
    security = HTTPBasic()
    logging.warning("HTTP Basic auth is required to connect to the web-service")
else:
    security = None
    logging.warning("!!!! HTTP Basic auth is NOT required to connect to the web-service !!!!")


# callback that is used on every request to check the auth-service caller's credentials
def authorize(credentials: HTTPBasicCredentials = Depends(security)):

    is_known_user = credentials.username in basic_auth_users
    is_pass_ok = False
    if is_known_user:
        is_pass_ok = secrets.compare_digest(credentials.password, basic_auth_users[credentials.username])
    else:
        # avoid timing attach and simulate a credentials comparison (but ignore the result)
        secrets.compare_digest(credentials.password, "wrong-password")

    if not (is_known_user and is_pass_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect username or password.',
            headers={'WWW-Authenticate': 'Basic'},
        )


if is_basic_auth_enabled:
    basic_auth_dependencies = [Depends(authorize)]
else:
    basic_auth_dependencies = []


# route to create tokens
@app.put("/tokens/{token_type}", dependencies=basic_auth_dependencies)
def create_token(token_type: str, request: TokenCreationRequest):
    try:
        if request.type is None:
            request.type = token_type
        elif request.type != token_type:
            raise HTTPException(status_code=400, detail="'type' field should match the url segment /tokens/{type}")

        logging.info("creating token: " + request.json())

        # transform the validity_duration into an expiration_date
        if request.expiration_date is None and request.validity_duration is not None:
            request.expiration_date = (pytz.UTC.localize(datetime.now()) + timedelta(seconds=request.validity_duration)).isoformat()

        token = token_service.create_token(request=request)

        logging.info("created token: " + token.json())
        return token

    except ValueError as ex:
        raise HTTPException(status_code=400, detail=str(ex))
    except Exception as ex:
        logging.exception(ex)
        raise HTTPException(status_code=500, detail=str(ex))


# route called by the Orthanc Authorization plugin to validate a token can access to a resource
@app.post("/tokens/validate", dependencies=basic_auth_dependencies)
def validate_authorization(request: TokenValidationRequest, token=Header(default=None)):

    try:
        logging.info("validating token: " + request.json())

        if request.token_value and not token:
            token = request.token_value

        granted = False
        if token is not None:  # token may be None for Anonymous requests (no tokens)

            if token.startswith("Bearer "):
                token = token.replace("Bearer ", "")

            granted = token_service.is_valid(
                token=token,
                orthanc_id=request.orthanc_id,
                dicom_uid=request.dicom_uid,
                server_id=request.server_id
            )

        response = TokenValidationResponse(
            granted=granted,
            validity=60
        )
        logging.info("validate token: " + response.json())
        return response

    except ValueError as ex:
        raise HTTPException(status_code=400, detail=str(ex))
    except Exception as ex:
        logging.exception(ex)
        raise HTTPException(status_code=500, detail=str(ex))


# route called by the Orthanc Authorization plugin to decode a token
@app.post("/tokens/decode", dependencies=basic_auth_dependencies)
def decode_token(request: TokenDecoderRequest):

    try:
        logging.info("decoding token: " + request.json())

        response = token_service.decode_token(
            token=request.token_value)

        logging.info("decoded token: " + response.json())
        return response

    except ValueError as ex:
        raise HTTPException(status_code=400, detail=str(ex))
    except Exception as ex:
        logging.exception(ex)
        raise HTTPException(status_code=500, detail=str(ex))


@app.post("/user/get-profile")  # this is a POST and not a GET because we want to same kind of payload as for other routes
def get_user_profile(user_profile_request: UserProfileRequest):
    logging.info("get user profile: " + user_profile_request.json())

    try:
        if user_profile_request.token_key is not None:
            response = get_user_profile_from_token(user_profile_request.token_value)

            # TODO get name and role from keycloak + transform roles into permissions

            response = UserProfileResponse(
                name="John Doe",
                permissions=[
                    UserPermissions.VIEW,
                    UserPermissions.DOWNLOAD,
                    UserPermissions.SEND,
                    UserPermissions.Q_R_REMOTE_MODALITIES,
                    UserPermissions.UPLOAD,
                    UserPermissions.SHARE
                ],
                validity=60
            )
        else:
            response = UserProfileResponse(
                name="Anonymous",
                permissions=[],
                validity=60
            )

        return response
    except jwt.exceptions.InvalidAlgorithmError:
        response = UserProfileResponse(
            name="Not a user token",
            permissions=[],
            validity=60
        )
        return response


def get_user_profile_from_token(jwt_token: str) -> UserProfileResponse:
    decoded_token = decode_token(jwt_token=jwt_token)
    response = UserProfileResponse(name="", permissions=[], validity=60)

    response.name = get_name_from_decoded_token(decoded_token=decoded_token)

    roles = get_roles_from_decoded_token(decoded_token=decoded_token)

    response.permissions = get_permissions_from_roles(roles)

    return response


def get_permissions_from_roles(roles: List[str]) -> List[UserPermissions]:
    response = []

    # for each role received from the token sent by Keycloak
    for role in roles:
        # search for it in the configured roles
        configured_role = configured_roles.get(role)
        # if it has been configured:
        if configured_role is not None:
            # Let's add the permissions in the response
            for item in configured_role:
                # (if not already there)
                if UserPermissions(item) not in response:
                    response.append(UserPermissions(item))

    return response


def get_roles_from_decoded_token(decoded_token: str) -> List[str]:
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


def get_name_from_decoded_token(decoded_token: str) -> str:
    name = decoded_token.get('name')
    if name is not None:
        return name
    return ''


def decode_token(jwt_token: str) -> str:
    return jwt.decode(jwt=jwt_token, key=public_key, audience="account", algorithms=["RS256"])


def get_keycloak_public_key(keycloak_uri: str) -> str:
    '''
    - get public key from keycloak server
    - add "-----BEGIN PUBLIC KEY-----" (and same for the end)
    - return it as a bytes string
    '''

    public_key = requests.get(keycloak_uri).json().get("public_key")

    begin_public_key = "-----BEGIN PUBLIC KEY-----\n"
    end_public_key = "\n-----END PUBLIC KEY-----"

    return ''.join([begin_public_key, public_key, end_public_key]).encode()


def get_config_from_file(file_path: str):
    with open(file_path) as f:
        data = json.load(f)
    return data.get('roles')




# get these values once for all
keycloak_uri = os.environ.get("KEYCLOAK_URI", "http://keycloak:8080/realms/orthanc-realm/")
permissions_file_path = os.environ.get("PERMISSIONS_FILE_PATH", "permissions.json")

try:
    public_key = get_keycloak_public_key(keycloak_uri)
    logging.info(f"Got the public key from Keycloak.")

except Exception as ex:
    logging.exception(ex)
    logging.error(f"Unable to reach keycloak (be patient, Keycloak may need more than 1 min to start), exiting...")
    exit(-1)

try:
    configured_roles = get_config_from_file(permissions_file_path)
    logging.info(f"Got the roles and permissions from configuration file")

except Exception as ex:
    logging.exception(ex)
    logging.error(f"Unable to get roles and permissions from configuration file ({permissions_file_path}), exiting...")
    exit(-1)
