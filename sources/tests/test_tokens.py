import datetime

from orthanc_share import Hs256TokensManager, TokensManager, ShareRequest, ShareType, ShareValidationRequest

import unittest
import subprocess
import pytz
import pathlib

import os

here = pathlib.Path(__file__).parent.resolve()



class TestTokensGenerator(unittest.TestCase):

    def test_hs_256_nominal_no_expiration_date(self):
        # create a token
        share_request = ShareRequest(
            id="id",
            orthanc_id="orthanc_id",
            dicom_uid="dicom_uid",
            type=ShareType.osimis_viewer_link
        )
        tokens = Hs256TokensManager(secret_key="toto")
        token = tokens.generate_token(share_request=share_request)

        self._test_tokens(token, tokens)

    def test_hs_256_nominal_with_expiration_date(self):
        # create a token
        share_request = ShareRequest(
            id="id",
            orthanc_id="orthanc_id",
            dicom_uid="dicom_uid",
            type=ShareType.osimis_viewer_link,
            expiration_date=pytz.UTC.localize(datetime.datetime(2100, 12, 31, 0, 0, 0))
        )
        tokens = Hs256TokensManager(secret_key="toto")
        token = tokens.generate_token(share_request=share_request)

        self._test_tokens(token, tokens)

    def test_hs_256_nominal_with_expired_expiration_date(self):
        # create a token
        share_request = ShareRequest(
            id="id",
            orthanc_id="orthanc_id",
            dicom_uid="dicom_uid",
            type=ShareType.osimis_viewer_link,
            expiration_date=pytz.UTC.localize(datetime.datetime(2000, 12, 31, 0, 0, 0))
        )
        tokens = Hs256TokensManager(secret_key="toto")
        token = tokens.generate_token(share_request=share_request)

        self.assertFalse(tokens.is_valid(
            token=token,
            dicom_uid="dicom_uid",
            orthanc_id="orthanc_id"
        ))


    def _test_tokens(self, token: str, tokens: TokensManager):
        #validate the token with the same manager, both ids identical
        self.assertTrue(tokens.is_valid(
            token=token,
            dicom_uid="dicom_uid",
            orthanc_id="orthanc_id"
        ))

        #one id missing -> still valid
        self.assertTrue(tokens.is_valid(
            token=token,
            dicom_uid="dicom_uid",
            orthanc_id=None
        ))

        #other id missing -> still valid
        self.assertTrue(tokens.is_valid(
            token=token,
            dicom_uid=None,
            orthanc_id="orthanc_id"
        ))

        #both ids missing -> not valid
        self.assertFalse(tokens.is_valid(
            token=token,
            dicom_uid=None,
            orthanc_id=None
        ))

        #another id -> invalid
        self.assertFalse(tokens.is_valid(
            token=token,
            dicom_uid=None,
            orthanc_id="not a valid id"
        ))

        #another id -> invalid
        self.assertFalse(tokens.is_valid(
            token=token,
            dicom_uid="not a valid id",
            orthanc_id=None
        ))

        #a valid id and an invalid id -> invalid
        self.assertFalse(tokens.is_valid(
            token=token,
            dicom_uid="not a valid id",
            orthanc_id="orthanc_id"
        ))

        split_token = token.split(".")

        #alter the first part of the token -> invalid
        altered_token = (split_token[0][1:] + "." + split_token[1] + "." + split_token[2]).encode('utf-8')
        self.assertFalse(tokens.is_valid(
            token=altered_token,
            dicom_uid="dicom_uid"
        ))

        #alter the second part of the token -> invalid
        altered_token = (split_token[0] + "." + split_token[1][1:] + "." + split_token[2]).encode('utf-8')
        self.assertFalse(tokens.is_valid(
            token=altered_token,
            dicom_uid="dicom_uid"
        ))

        #alter the third part of the token -> invalid
        altered_token = (split_token[0][1:] + "." + split_token[1] + "." + split_token[2][1:]).encode('utf-8')
        self.assertFalse(tokens.is_valid(
            token=altered_token,
            dicom_uid="dicom_uid"
        ))
