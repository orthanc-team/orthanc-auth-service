from fastapi import FastAPI, Request, status, Header
from dateutil import parser
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from flask import Flask, jsonify, request
import json
from enum import Enum
from typing import Union
from fastapi import FastAPI
from pydantic import BaseModel, Field
from pydantic.datetime_parse import parse_datetime
from datetime import datetime
import jwt
import pytz

# TODO: get this from an env variable !!!
secret_key="toto"


class StringDateTime(datetime):
    @classmethod
    def __get_validators__(cls):
        yield parse_datetime
        yield cls.validate

    @classmethod
    def validate(cls, v: datetime):
        return v.isoformat()


class ShareType(str, Enum):
    osimis_viewer_link = 'osimis-viewer-publication'


class ShareRequest(BaseModel):
    id: str
    dicom_uid: Union[str, None] = Field(alias="dicom-uid", default=None)
    orthanc_id: Union[str, None] = Field(alias="orthanc-id", defulat=None)
    type: ShareType
    expiration_date: Union[StringDateTime, None] = None

    class Config:    # allow creating object from dict (used when deserializing the JWT)
        allow_population_by_field_name = True

class Share(BaseModel):
    request: ShareRequest
    token: str


class AuthValidationRequest(BaseModel):
    dicom_uid: Union[str, None] = Field(alias="dicom-uid", default=None)
    orthanc_id: Union[str, None] = Field(alias="orthanc-id", defulat=None)
    level: str
    method: str


class AuthValidationResponse(BaseModel):
    granted: bool
    validity: int


app = FastAPI()

# @app.exception_handler(RequestValidationError)
# async def validation_exception_handler(request: Request, exc: RequestValidationError):
#     exc_str = f'{exc}'.replace('\n', ' ').replace('   ', ' ')
#     # or logger.error(f'{exc}')
#     # logger.error(request, exc_str)
#     content = {'status_code': 422, 'message': exc_str, 'data': None}
#     return JSONResponse(content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


# route to create shares
@app.put("/shares")
def create_share(share_request: ShareRequest):

    encoded = jwt.encode(share_request.dict(), secret_key, algorithm="HS256")

    share = Share(request=share_request, token=encoded)

    return share

@app.post("/auth/validate")
def validate_authorization(validation_request: AuthValidationRequest, token = Header(default=None)):

    r = jwt.decode(token, secret_key, algorithms="HS256")
    share_request = ShareRequest(**r)

    granted = (share_request.dicom_uid == validation_request.dicom_uid) or (share_request.orthanc_id == validation_request.orthanc_id)

    expiration_date = parser.parse(share_request.expiration_date)
    now_utc = pytz.UTC.localize(datetime.now())

    # check expiration date
    granted = granted and (now_utc < expiration_date)

    response = AuthValidationResponse(granted=granted, validity=60)
    return response
