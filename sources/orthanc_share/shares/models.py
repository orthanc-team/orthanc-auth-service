from typing import Optional, List
from pydantic import BaseModel, Field
from pydantic.datetime_parse import parse_datetime
from enum import Enum
from datetime import datetime


class StringDateTime(datetime):
    @classmethod
    def __get_validators__(cls):
        yield parse_datetime
        yield cls.validate

    @classmethod
    def validate(cls, v: datetime):
        return v.isoformat()


class Levels(str, Enum):
    PATIENT = 'patient'
    STUDY = 'study'
    SERIES = 'series'
    INSTANCE = 'instance'

    SYSTEM = 'system'


class Methods(str, Enum):
    GET = 'get'
    POST = 'post'
    PUT = 'put'
    DELETE = 'delete'


class TokenType(str, Enum):
    OSIMIS_VIEWER_PUBLICATION = 'osimis-viewer-publication'  # a link to open the Osimis viewer valid for a long period
    MEDDREAM_VIEWER_PUBLICATION = 'meddream-viewer-publication'  # a link to open the MedDream viewer valid for a long period
    STONE_VIEWER_PUBLICATION = 'stone-viewer-publication'  # a link to open the Stone viewer valid for a long period

    MEDDREAM_INSTANT_LINK = 'meddream-instant-link'  # a direct link to MedDream viewer that is valid only a few minutes to open the viewer directly

    # OSIMIS_VIEWER_INSTANT_LINK = 'osimis-viewer-instant-link'  # a direct link to Osimis viewer that is valid only a few minutes to open the viewer directly
    # STONE_VIEWER_INSTANT_LINK = 'stone-viewer-instant-link'  # a direct link to Stone viewer that is valid only a few minutes to open the viewer directly
    #
    # DOWNLOAD_INSTANT_LINK = 'download-instant-link'  # a link to download a study/series/instance directly
    VIEWER_INSTANT_LINK = 'viewer-instant-link'             # a link to a resource to be used directly.
    DOWNLOAD_INSTANT_LINK = 'download-instant-link'         # a link to a resource to be used directly.


    INVALID = 'invalid'

class OrthancResource(BaseModel):
    dicom_uid: Optional[str] = Field(alias="dicom-uid", default=None)
    orthanc_id: Optional[str] = Field(alias="orthanc-id", default=None)
    url: Optional[str] = None                                                       # e.g. a download link /studies/.../archive
    level: Levels

    class Config:  # allow creating object from dict (used when deserializing the JWT)
        allow_population_by_field_name = True


class TokenCreationRequest(BaseModel):
    id: Optional[str] = None
    resources: List[OrthancResource]
    type: TokenType = Field(default=TokenType.INVALID)
    expiration_date: Optional[StringDateTime] = Field(alias="expiration-date", default=None)

    class Config:  # allow creating object from dict (used when deserializing the JWT)
        allow_population_by_field_name = True


class TokenCreationResponse(BaseModel):
    request: TokenCreationRequest
    token: str
    url: Optional[str] = None


class TokenValidationRequest(BaseModel):
    dicom_uid: Optional[str] = Field(alias="dicom-uid", default=None)
    orthanc_id: Optional[str] = Field(alias="orthanc-id", default=None)
    token_key: Optional[str] = Field(alias="token-key", default=None)
    token_value: Optional[str] = Field(alias="token-value", default=None)
    server_id: Optional[str] = Field(alias="server-id", default=None)
    level: Optional[Levels]
    method: Methods
    uri: Optional[str]


class TokenValidationResponse(BaseModel):
    granted: bool
    validity: int


class UserProfileRequest(BaseModel):
    token_key: Optional[str] = Field(alias="token-key", default=None)
    token_value: Optional[str] = Field(alias="token-value", default=None)
    server_id: Optional[str] = Field(alias="server-id", default=None)


class UserPermissions(str, Enum):
    VIEW = 'view'
    DOWNLOAD = 'download'
    DELETE = 'delete'
    SEND = 'send'
    MODIFY = 'modify'
    ANONYMIZE = 'anonymize'
    UPLOAD = 'upload'
    Q_R_REMOTE_MODALITIES = 'q-r-remote-modalities'
    SETTINGS = 'settings'
    API_VIEW = 'api-view'
    LEGACY_UI = 'legacy-ui'

    SHARE = 'share'


class UserProfileResponse(BaseModel):
    name: str
    permissions: List[UserPermissions] = Field(default_factory=list)
    validity: int

    class Config:
        use_enum_values = True