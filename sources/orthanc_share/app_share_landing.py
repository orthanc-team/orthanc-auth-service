from fastapi import FastAPI, Request, status, Header, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
import logging
from shares.models import *
from shares.orthanc_token_service_factory import create_token_service_from_secrets
from shares.exceptions import *

logging.basicConfig(level=logging.DEBUG)

token_service = create_token_service_from_secrets()
app = FastAPI()


def html_response(msg: str) -> HTMLResponse:
    html_content = f"<html><body><h1>{msg}</h1></body></html>"
    return HTMLResponse(content=html_content, status_code=200)

# route used as a landing page to check tokens, display a nice error message and redirect to the final viewer
@app.get("/share-landing/")
def landing_page(token: str = None):

    try:
        logging.info("Shares landing: " + token)

        share_request = token_service.get_share_request_from_token(token=token) #this will raise if the token can not be decoded

        if token_service.is_expired(share_request):
            return html_response("Your token has expired")

        # we can not check that the token is valid for the given study, this will be check by the auth plugin once the viewer opens

        redirect_url = token_service.redirect_to_viewer(token=token)
        return RedirectResponse(redirect_url)

    except InvalidTokenException as ex:
        logging.exception(ex)
        return html_response("Your token is not valid")
    except SharesException as ex:
        logging.exception(ex)
        return html_response("An internal error has occured (1)")
    except Exception as ex:
        logging.exception(ex)
        return html_response("An internal error has occured (2)")
