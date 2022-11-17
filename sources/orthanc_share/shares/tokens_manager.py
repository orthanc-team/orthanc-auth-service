# SPDX-FileCopyrightText: 2022 Orthanc Team SRL <info@orthanc.team>
#
# SPDX-License-Identifier: GPL-3.0-or-later

from .models import *
from .exceptions import *
from typing import Optional, List

import logging

logging.basicConfig(level=logging.INFO)


class TokensManager:
    anonymized_server_identifier_: Optional[str] = None
    standard_server_identifier_: Optional[str] = None

    def _encode_token(self, share_request: ShareRequest) -> str:
        return None # to override in derived class

    def _decode_token(self, token) -> dict:
        return None # to override in derived class

    def generate_token(self, share_request: ShareRequest) -> str:
        return self._encode_token(share_request)

    def get_share_request_from_token(self, token: str) -> ShareRequest:
        r = self._decode_token(token)
        return ShareRequest(**r)

    def is_expired(self, share_request: ShareRequest) -> bool:
        # check expiration date
        if share_request.expiration_date:
            expiration_date = parser.parse(share_request.expiration_date)
            now_utc = pytz.UTC.localize(datetime.now())

            is_valid = now_utc < expiration_date
            if not is_valid:
                logging.warning(f"Token Validation: period is invalid")
            return not is_valid

        return False


    def is_valid(self, token: str, orthanc_id: Optional[str] = None, dicom_uid: Optional[str] = None, server_identifier: Optional[str] = None) -> bool:

        # no ids to check, we consider it's invalid
        if not dicom_uid and not orthanc_id:
            logging.warning(f"Token Validation: no ids found")
            return False

        try:
            logging.warning(f"decoding")
            r = self._decode_token(token)
            logging.warning(f"decoded")
            share_request = ShareRequest(**r)
        except:
            logging.warning(f"Token Validation: failed to decode token")
            return False

        granted = False

        # check the ids.  The share_request might have been generated with 2 ids
        share_request_has_dicom_uids = all([s.dicom_uid is not None for s in share_request.studies])
        share_request_has_orthanc_ids = all([s.orthanc_id is not None for s in share_request.studies])
        # but when we check, we'll probably only have a single ID (the orthanc_id for Orthanc Rest API and the dicom_uid for DicomWeb)
        if dicom_uid and share_request_has_dicom_uids:
            granted = any([s.dicom_uid == dicom_uid for s in share_request.studies])
            if not granted:
                all_dicom_uids = ", ".join([s.dicom_uid for s in share_request.studies])
                logging.warning(f"Token Validation: invalid dicom_uid, from request: {dicom_uid}, from token: {all_dicom_uids}")
                return False

        if orthanc_id and share_request_has_orthanc_ids:
            granted = any([s.orthanc_id == orthanc_id for s in share_request.studies])
            if not granted:
                all_orthanc_ids = ", ".join([s.orthanc_id for s in share_request.studies])
                logging.warning(f"Token Validation: invalid orthanc_id, from request: {orthanc_id}, from token: {all_orthanc_ids}")
                return False

        # check the server identifier
        if share_request.anonymized and self.anonymized_server_identifier_:
            server_id_is_valid = server_identifier == self.anonymized_server_identifier_
            if not server_id_is_valid:
                logging.warning(f"Token Validation: invalid anonymized_server_identifier")
            granted = granted and server_id_is_valid

        if not share_request.anonymized and self.standard_server_identifier_:
            server_id_is_valid = server_identifier == self.standard_server_identifier_
            if not server_id_is_valid:
                logging.warning(f"Token Validation: invalid server_identifier")
            granted = granted and server_id_is_valid

        # check expiration date
        granted = granted and not self.is_expired(share_request)

        return granted


class Hs256TokensManager(TokensManager):

    secret_key_: str

    def __init__(self, secret_key: str, standard_server_identifier: Optional[str] = None, anonymized_server_identifier: Optional[str] = None):
        self.secret_key_ = secret_key
        self.standard_server_identifier_ = standard_server_identifier
        self.anonymized_server_identifier_ = anonymized_server_identifier

    def _encode_token(self, share_request: ShareRequest) -> str:
        return jwt.encode(share_request.dict(), self.secret_key_, algorithm="HS256")

    def _decode_token(self, token: str) -> dict:
        try:
            return jwt.decode(token, self.secret_key_, algorithms="HS256")
        except jwt.exceptions.InvalidTokenError:
            raise InvalidTokenException

