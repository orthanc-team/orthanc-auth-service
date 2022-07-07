from fastapi import FastAPI, Request, status, Header
from dateutil import parser

from enum import Enum
from typing import Union
from fastapi import FastAPI
from pydantic import BaseModel, Field
from pydantic.datetime_parse import parse_datetime
from datetime import datetime
import os
import jwt
import pytz
import logging


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
    url: str


class ShareValidationRequest(BaseModel):
    dicom_uid: Union[str, None] = Field(alias="dicom-uid", default=None)
    orthanc_id: Union[str, None] = Field(alias="orthanc-id", default=None)
    level: str
    method: str


class ShareValidationResponse(BaseModel):
    granted: bool
    validity: int
