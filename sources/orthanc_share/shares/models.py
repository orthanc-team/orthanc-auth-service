# SPDX-FileCopyrightText: 2022 Orthanc Team SRL <info@orthanc.team>
#
# SPDX-License-Identifier: GPL-3.0-or-later

from fastapi import FastAPI, Request, status, Header
from dateutil import parser

from enum import Enum
from typing import Union, Optional, List
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
    osimis_viewer_publication = 'osimis-viewer-publication'         # a link to open the Osimis viewer valid for a long period
    meddream_instant_link = 'meddream-instant-link'                 # a direct link to MedDream viewer that is valid only a few minutes for immediate publication
    meddream_viewer_publication = 'meddream-viewer-publication'     # a link to open the MedDream viewer valid for a long period
    stone_viewer_publication = 'stone-viewer-publication'           # a link to open the Stone viewer valid for a long period


class SharedStudy(BaseModel):
    dicom_uid: Optional[str] = Field(alias="dicom-uid", default=None)
    orthanc_id: Optional[str] = Field(alias="orthanc-id", default=None)

    class Config:    # allow creating object from dict (used when deserializing the JWT)
        allow_population_by_field_name = True


class ShareRequest(BaseModel):
    id: Optional[str] = None
    studies: List[SharedStudy]
    anonymized: bool = False
    type: ShareType
    expiration_date: Optional[StringDateTime] = Field(alias="expiration-date", default=None)

    class Config:    # allow creating object from dict (used when deserializing the JWT)
        allow_population_by_field_name = True


class Share(BaseModel):
    request: ShareRequest
    token: str
    url: str


class ShareValidationRequest(BaseModel):
    dicom_uid: Optional[str] = Field(alias="dicom-uid", default=None)
    orthanc_id: Optional[str] = Field(alias="orthanc-id", default=None)
    token_key: Optional[str] = Field(alias="token-key", default=None)
    token_value: Optional[str] = Field(alias="token-value", default=None)
    identifier: Optional[str]
    level: str
    method: str


class ShareValidationResponse(BaseModel):
    granted: bool
    validity: int
