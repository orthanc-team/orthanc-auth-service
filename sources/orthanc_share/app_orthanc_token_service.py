from fastapi import FastAPI, Request, status, Header, HTTPException, Depends
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import logging
import urllib.parse
import httpx
import json
import secrets
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


# callback that is used on every request to check the caller's credentials
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


# route to create shares
@app.put("/shares", dependencies=basic_auth_dependencies)
def create_share(share_request: ShareRequest):
    try:
        logging.info("creating share: " + share_request.json())

        share = token_service.create_share(share_request=share_request)

        logging.info("created share: " + share.json())
        return share

    except ValueError as ex:
        raise HTTPException(status_code=400, detail=str(ex))
    except Exception as ex:
        logging.exception(ex)
        raise HTTPException(status_code=500, detail=str(ex))


# route called by the Orthanc Authorization plugin to validate a token can access to a resource
@app.post("/shares/validate", dependencies=basic_auth_dependencies)
def validate_authorization(validation_request: ShareValidationRequest, token=Header(default=None)):

    try:
        logging.info("validating share: " + validation_request.json())

        if validation_request.token_value and not token:
            token = validation_request.token_value

        if token.startswith("Bearer "):
            token = token.replace("Bearer ", "")

        response = ShareValidationResponse(
            granted=token_service.is_valid(
                token=token,
                orthanc_id=validation_request.orthanc_id,
                dicom_uid=validation_request.dicom_uid,
                server_identifier=validation_request.identifier
            ),
            validity=60
        )
        logging.info("validate share: " + response.json())
        return response

    except ValueError as ex:
        raise HTTPException(status_code=400, detail=str(ex))
    except Exception as ex:
        logging.exception(ex)
        raise HTTPException(status_code=500, detail=str(ex))

