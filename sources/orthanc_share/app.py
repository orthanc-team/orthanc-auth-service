from fastapi import FastAPI, Request, status, Header
import logging
import urllib.parse
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


    if share_request.type == ShareType.osimis_viewer_link:
        if share_request.orthanc_id is None:
            logging.error("No orthanc_id provided while generating a link to the Osimis WebViewer")
            return None

        return urllib.parse.urljoin(public_orthanc_root, f"osimis-viewer/app/index.html?study={share_request.orthanc_id}&token={token}")


# @app.middleware("http")
# async def add_process_time_header(request: Request, call_next):
#
#     response = await call_next(request)
#     logging.error(response)
#     return response


# route to create shares
@app.put("/shares")
def create_share(share_request: ShareRequest):
    logging.info("creating share: " + share_request.json())

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
