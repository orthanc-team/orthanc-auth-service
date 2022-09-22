import os

from fastapi import FastAPI, Request, status, Header, HTTPException
from fastapi.responses import RedirectResponse
import logging
import urllib.parse
import httpx
import pprint
from models import *
from tokens import Hs256TokensManager

logging.basicConfig(level=logging.DEBUG)


# try to read a secret first from a secret file or from an env var.
# stop execution if not
def get_secret_or_die(name: str):
    secret_file_path = f"/run/secrets/{name}"
    if os.path.exists(secret_file_path) and os.path.isfile(secret_file_path):
        with open(secret_file_path, "rt") as secret_file:
            return secret_file.read().strip()

    if os.environ.get(name) is not None:
        return os.environ.get(name)

    logging.error(f"Secret '{name}' is not defined, can not start without it")
    exit(-1)


secret_key = get_secret_or_die("SECRET_KEY")
public_orthanc_root = get_secret_or_die("PUBLIC_ORTHANC_ROOT")

enable_meddream_shares = os.environ.get("ENABLE_MEDDREAM_SHARES", "false").lower() == "true"
enable_meddream_instance_links = os.environ.get("ENABLE_MEDDREAM_INSTANT_LINKS", "false").lower() == "true"

if enable_meddream_shares:
    enable_meddream_instance_links = True  # we need the instant links !
    public_meddream_redirect_root = get_secret_or_die("PUBLIC_MEDDREAM_REDIRECT_ROOT")

if enable_meddream_instance_links:
    meddream_token_service_url = get_secret_or_die("MEDDREAM_TOKEN_SERVICE_URL")
    public_meddream_root = get_secret_or_die("PUBLIC_MEDDREAM_ROOT")

    if not public_meddream_root.endswith('/'):
        logging.error("PUBLIC_MEDDREAM_ROOT should end with a '/'")
        exit(-1)



tokens = Hs256TokensManager(secret_key=secret_key)

app = FastAPI()

# @app.exception_handler(RequestValidationError)
# async def validation_exception_handler(request: Request, exc: RequestValidationError):
#     exc_str = f'{exc}'.replace('\n', ' ').replace('   ', ' ')
#     # or logger.error(f'{exc}')
#     # logger.error(request, exc_str)
#     content = {'status_code': 422, 'message': exc_str, 'data': None}
#     return JSONResponse(content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

def generate_url(share_request: ShareRequest, token: str):
    global public_orthanc_root
    global public_meddream_root

    if share_request.type == ShareType.osimis_viewer_publication:
        if share_request.orthanc_id is None:
            logging.error("No orthanc_id provided while generating a link to the Osimis WebViewer")
            return None

        return urllib.parse.urljoin(public_orthanc_root, f"osimis-viewer/app/index.html?study={share_request.orthanc_id}&token={token}")

    elif share_request.type == ShareType.meddream_instant_link:
        if share_request.dicom_uid is None:
            logging.error("No dicom_uid provided while generating a link to the MedDream Viewer")
            return None

        if public_meddream_root is None:
            logging.error("MEDDREAM_PUBLIC_ROOT is not defined, can not generate MedDream instant tokens")
            raise HTTPException(status_code=500, detail="MEDDREAM_ROOT is not defined")

        return urllib.parse.urljoin(public_meddream_root, f"?token={token}")

    elif share_request.type == ShareType.meddream_viewer_publication:
        return urllib.parse.urljoin(public_meddream_redirect_root, f"?token={token}")

# @app.middleware("http")
# async def add_process_time_header(request: Request, call_next):
#
#     response = await call_next(request)
#     logging.error(response)
#     return response


# route to create shares
@app.put("/shares")
def create_share(share_request: ShareRequest):
    global meddream_token_service_url

    logging.info("creating share: " + share_request.json())

    if share_request.type == ShareType.osimis_viewer_publication:
        token = tokens.generate_token(share_request=share_request)

    if enable_meddream_shares:
        if share_request.type == ShareType.meddream_instant_link:
            # for the instant link, we get the token directly from the meddream token service
            if meddream_token_service_url is None:
                logging.error("MEDDREAM_TOKEN_SERVICE_URL is not defined, can not generate MedDream tokens")
                raise HTTPException(status_code=500, detail="MEDDREAM_TOKEN_SERVICE_URL is not defined")

            token = httpx.post(meddream_token_service_url, json={
                "items": [{
                    "studies": {
                        "study": share_request.dicom_uid,
                        "storage": "Orthanc"
                    }
                }]
            }).text

        elif share_request.type == ShareType.meddream_viewer_publication:
            # we do not generate a meddream token now, this will be handled by the meddread-share-redirect service at the time we try to access the link

            if share_request.dicom_uid is None:
                logging.error("No dicom_uid provided while generating a link to the MedDream Viewer")
                raise HTTPException(status_code=400, detail="No dicom_uid provided while generating a link to the MedDream Viewer")

            token = tokens.generate_token(share_request=share_request)

    share = Share(
        request=share_request,
        token=token,
        url=generate_url(
            share_request=share_request,
            token=token
        )
    )
    logging.info("created share: " + share.json())
    return share

# route called by the Orthanc Authorization plugin to validate a token has access to a resource
@app.post("/shares/validate")
def validate_authorization(validation_request: ShareValidationRequest, token = Header(default=None)):
    logging.info("validating share: " + validation_request.json())

    # TODO: check token-key & token-value

    response = ShareValidationResponse(
        granted=tokens.is_valid(
            token=token,
            orthanc_id=validation_request.orthanc_id,
            dicom_uid=validation_request.dicom_uid
        ),
        validity=60
    )
    logging.info("validate share: " + response.json())
    return response


# route used to redirect meddream-shares and generate meddream token on the fly
@app.get("/meddream-redirect/")
def redirect_meddream(token: str = None):

    logging.info("meddream redirect: " + token)

    # extract the initial share request from the token
    share_request = tokens.get_share_request_from_token(token=token)

    # check it is valid (this actually only checks the expiration date since we get the ids from the request itself !)
    if tokens.is_valid(token=token,orthanc_id=share_request.orthanc_id,dicom_uid=share_request.dicom_uid):
        # generate a new meddream token that will be valid for only a few minutes
        share_request.type = ShareType.meddream_instant_link
        share = create_share(share_request)

        # redirect to meddream viewer with this new token
        return RedirectResponse(share.url)

    return HTTPException(400, "Token is not valid")