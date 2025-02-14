# SPDX-FileCopyrightText: 2022 - 2025 Orthanc Team SRL <info@orthanc.team>
#
# SPDX-License-Identifier: GPL-3.0-or-later

from .models import *
from .exceptions import *
from typing import Optional, List

import logging
import pytz
import jwt
from .utils.utils import DateTimeJSONEncoder

logging.basicConfig(level=logging.INFO)


class TokensManager:
    server_id_: Optional[str] = None

    def _encode_token(self, request: TokenCreationRequest) -> str:
        return None # to override in derived class

    def _decode_token(self, token) -> dict:
        return None # to override in derived class

    def generate_token(self, request: TokenCreationRequest) -> str:
        return self._encode_token(request)

    def get_request_from_token(self, token: str) -> TokenCreationRequest:
        r = self._decode_token(token)
        return TokenCreationRequest(**r)

    def is_expired(self, request: TokenCreationRequest) -> bool:
        # check expiration date
        if request.expiration_date:
            now_utc = pytz.UTC.localize(datetime.now())

            is_valid = now_utc < request.expiration_date
            if not is_valid:
                logging.warning(f"Token Validation: period is invalid")
            return not is_valid

        return False


    def is_valid(self, token: str, orthanc_id: Optional[str] = None, dicom_uid: Optional[str] = None, server_id: Optional[str] = None) -> bool:

        # no ids to check, we consider it's invalid
        if not dicom_uid and not orthanc_id:
            logging.warning(f"Token Validation: no ids found")
            return False

        try:
            r = self._decode_token(token)
            share_request = TokenCreationRequest(**r)
        except Exception as ex:
            logging.warning(f"Token Validation: failed to decode token")
            return False

        granted = False

        # check the ids.  The share_request might have been generated with 2 ids
        share_request_has_dicom_uids = all([s.dicom_uid is not None for s in share_request.resources])
        share_request_has_orthanc_ids = all([s.orthanc_id is not None for s in share_request.resources])
        # but when we check, we'll probably only have a single ID (the orthanc_id for Orthanc Rest API and the dicom_uid for DicomWeb)
        if dicom_uid and share_request_has_dicom_uids:
            granted = any([s.dicom_uid == dicom_uid for s in share_request.resources])
            if not granted:
                all_dicom_uids = ", ".join([s.dicom_uid for s in share_request.resources])
                logging.warning(f"Token Validation: invalid dicom_uid, from request: {dicom_uid}, from token: {all_dicom_uids}")
                return False

        if orthanc_id and share_request_has_orthanc_ids:
            granted = any([s.orthanc_id == orthanc_id for s in share_request.resources])
            if not granted:
                all_orthanc_ids = ", ".join([s.orthanc_id for s in share_request.resources])
                logging.warning(f"Token Validation: invalid orthanc_id, from request: {orthanc_id}, from token: {all_orthanc_ids}")
                return False

        if self.server_id_:
            server_id_is_valid = server_id == self.server_id_
            if not server_id_is_valid:
                logging.warning(f"Token Validation: invalid server_id")
            granted = granted and server_id_is_valid

        # check expiration date
        granted = granted and not self.is_expired(share_request)

        return granted


class Hs256TokensManager(TokensManager):

    secret_key_: str

    def __init__(self, secret_key: str, server_id: Optional[str] = None):
        self.secret_key_ = secret_key
        self.server_id_ = server_id

    def _encode_token(self, request: TokenCreationRequest) -> str:
        return jwt.encode(request.model_dump(), self.secret_key_, algorithm="HS256", json_encoder=DateTimeJSONEncoder)

    def _decode_token(self, token: str) -> dict:
        try:
            return jwt.decode(token, self.secret_key_, algorithms="HS256")
        except jwt.exceptions.InvalidTokenError:
            raise InvalidTokenException

