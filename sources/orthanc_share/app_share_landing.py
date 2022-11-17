# SPDX-FileCopyrightText: 2022 Orthanc Team SRL <info@orthanc.team>
#
# SPDX-License-Identifier: GPL-3.0-or-later

from fastapi import FastAPI, Request, status, Header, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import logging
import os
from shares.models import *
from shares.orthanc_token_service_factory import create_token_service_from_secrets
from shares.exceptions import *

logging.basicConfig(level=logging.DEBUG)

token_service = create_token_service_from_secrets()
app = FastAPI()

templates = Jinja2Templates(directory="landing-pages")

title_expired_token = os.environ.get("TITLE_EXPIRED_TOKEN", "Expired token")
message_expired_token = os.environ.get("MESSAGE_EXPIRED_TOKEN", "Your token has expired.<br/>You should ask for a new one.")
title_invalid_token = os.environ.get("TITLE_INVALID_TOKEN", "Invalid token")
message_invalid_token = os.environ.get("MESSAGE_INVALID_TOKEN", "Your token is invalid.<br/>Please check that you have copied it entirely.")


def generic_html_response(request: Request, title: str, message: str, custom_file: str) -> HTMLResponse:
    custom_file_path = os.path.join("landing-pages", custom_file)
    if os.path.exists(custom_file_path):
        with open(custom_file_path, "rb") as f:
            content = f.read()
            return HTMLResponse(content=content, status_code=200)

    return templates.TemplateResponse("generic-message.html", {
        "request": request,
        "title": title,
        "message": message
    })

# route used as a landing page to check tokens, display a nice error message and redirect to the final viewer
@app.get("/share-landing/")
def landing_page(request: Request, token: str = None):

    try:
        logging.info("Shares landing: " + token)

        share_request = token_service.get_share_request_from_token(token=token) #this will raise if the token can not be decoded

        if token_service.is_expired(share_request):
            return generic_html_response(request=request, title=title_expired_token, message=message_expired_token, custom_file="expired-token.html")

        # we can not check that the token is valid for the given study, this will be check by the auth plugin once the viewer opens

        redirect_url = token_service.redirect_to_viewer(token=token)
        return RedirectResponse(redirect_url)

    except InvalidTokenException as ex:
        logging.exception(ex)
        return generic_html_response(request=request, title=title_invalid_token, message=message_invalid_token, custom_file="invalid-token.html")

    except SharesException as ex:
        logging.exception(ex)
        return generic_html_response(request=request, title="Internal error", message="An internal error has occured (1)")

    except Exception as ex:
        logging.exception(ex)
        return generic_html_response(request=request, title="Internal error", message="An internal error has occured (2)")
