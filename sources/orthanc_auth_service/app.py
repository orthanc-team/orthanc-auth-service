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
from shares.keycloak import create_keycloak_from_secrets

logging.basicConfig(level=logging.DEBUG)

token_service = create_token_service_from_secrets()
keycloak = create_keycloak_from_secrets()
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

# to show invalid payloads (debug)
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
	exc_str = f'{exc}'.replace('\n', ' ').replace('   ', ' ')
	logging.error(f"{request}: {exc_str}")
	content = {'status_code': 10422, 'message': exc_str, 'data': None}
	return JSONResponse(content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

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


@app.post("/user/get-profile", dependencies=basic_auth_dependencies)  # this is a POST and not a GET because we want to same kind of payload as for other routes
def get_user_profile(user_profile_request: UserProfileRequest):
    logging.info("get user profile: " + user_profile_request.json())

    anonymous_profile = UserProfileResponse(
                name="Anonymous",
                permissions=[],
                authorized_labels=[],
                validity=60
            )
    try:
        if keycloak is None:
            logging.warning("Keycloak is not configured, all users are considered anonymous")
            return anonymous_profile
        elif user_profile_request.token_key is not None:
            response = keycloak.get_user_profile_from_token(user_profile_request.token_value)
        else:
            return anonymous_profile

        return response
    except jwt.exceptions.InvalidAlgorithmError:
        # not a valid user profile, consider it is anonymous
        return anonymous_profile
    except jwt.exceptions.PyJWTError:
        raise HTTPException(status_code=400, detail=str("Unable to decode token"))
    except Exception as ex:
        raise HTTPException(status_code=400, detail=str("Unexpected error: " + str(ex)))

