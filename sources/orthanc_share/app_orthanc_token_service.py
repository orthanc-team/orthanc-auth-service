# SPDX-FileCopyrightText: 2022 Orthanc Team SRL <info@orthanc.team>
#
# SPDX-License-Identifier: GPL-3.0-or-later

from fastapi import FastAPI, Request, status, Header, HTTPException, Depends, Query
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import logging
import urllib.parse
import json
import secrets
import os
import pprint
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


@app.post("/user/get-profile")  # this is a POST and not a GET because we want to same kind of payload as for other routes
def get_user_profile(user_profile_request: UserProfileRequest):
# def get_user_profile(token_key: str = Query(alias='token-key'),
#                      token_value: str = Query(alias='token-value'),
#                      server_id: Optional[str] = Query(alias='server-id', default=None)
#                      ):
#     user_profile_request = UserProfileRequest(
#         token_value=token_value,
#         token_key=token_key,
#         server_id=server_id)
    logging.info("get user profile: " + user_profile_request.json())

    # logging.info("token alone: " + validation_request.token_value)

    if user_profile_request.token_key is not None:
        # TODO get name and role from keycloak + transform roles into permissions

        response = UserProfileResponse(
            name="John Doe",
            permissions=[
                UserPermissions.VIEW,
                UserPermissions.DOWNLOAD,
                UserPermissions.SEND,
                UserPermissions.Q_R_REMOTE_MODALITIES,
                UserPermissions.UPLOAD,
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