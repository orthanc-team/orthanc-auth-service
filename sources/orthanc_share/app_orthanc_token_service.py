from fastapi import FastAPI, Request, status, Header, HTTPException
from fastapi.responses import RedirectResponse
import logging
import urllib.parse
import httpx
import pprint
from shares.models import *
from shares.orthanc_token_service_factory import create_token_service_from_secrets


logging.basicConfig(level=logging.DEBUG)

token_service = create_token_service_from_secrets()
app = FastAPI()




# route to create shares
@app.put("/shares")
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
@app.post("/shares/validate")
def validate_authorization(validation_request: ShareValidationRequest, token=Header(default=None)):

    try:
        logging.info("validating share: " + validation_request.json())

        # TODO: check token-key & token-value

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

