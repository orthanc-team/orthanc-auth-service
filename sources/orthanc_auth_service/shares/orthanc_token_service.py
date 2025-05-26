# SPDX-FileCopyrightText: 2022 - 2025 Orthanc Team SRL <info@orthanc.team>
#
# SPDX-License-Identifier: GPL-3.0-or-later

from .tokens_manager import Hs256TokensManager, TokensManager
from .models import *
import urllib
import httpx
import logging
from typing import Optional
from .exceptions import *


# this class generates JWT tokens that can be used by orthanc to access specific resources
class OrthancTokenService:

    tokens_manager_: TokensManager = None

    secret_key_: str

    public_orthanc_root_: Optional[str] = None
    public_ohif_root_: Optional[str] = None
    server_id_: Optional[str] = None
    ohif_data_source_: str = "dicom-web"

    meddream_token_service_url_: Optional[str] = None
    public_meddream_root_: Optional[str] = None
    public_landing_root_: Optional[str] = None

    def __init__(self, secret_key: str):
        self.secret_key_ = secret_key

    def _configure_server(self, public_orthanc_root: str, server_id: Optional[str] = None, public_landing_root: Optional[str] = None):
        self.public_orthanc_root_ = public_orthanc_root
        self.server_id_ = server_id
        self.public_landing_root_ = public_landing_root

    def _configure_meddream(self, meddream_token_service_url: str, public_meddream_root: str, public_landing_root: str):
        self.meddream_token_service_url_ = meddream_token_service_url
        self.public_meddream_root_ = public_meddream_root
        self.public_landing_root_ = public_landing_root

    def _configure_ohif(self, public_ohif_root: str, server_id: Optional[str] = None, public_landing_root: Optional[str] = None, ohif_data_source: str = "dicom-web"):
        self.public_ohif_root_ = public_ohif_root
        self.server_id_ = server_id
        self.public_landing_root_ = public_landing_root
        self.ohif_data_source_ = ohif_data_source

    def _create(self):
        if not self.tokens_manager_:
            self.tokens_manager_ = Hs256TokensManager(
                secret_key=self.secret_key_,
                server_id=self.server_id_
            )
        return self.tokens_manager_


    def _generate_url(self, request: TokenCreationRequest, token: str, skip_landing_page: bool = False):

        has_dicom_uids = all([s.dicom_uid is not None for s in request.resources])
        has_orthanc_ids = all([s.orthanc_id is not None for s in request.resources])

        if request.type == TokenType.OSIMIS_VIEWER_PUBLICATION:
            if not has_orthanc_ids:
                logging.error("No orthanc_id provided while generating a link to the Osimis WebViewer")
                return None

            if skip_landing_page or self.public_landing_root_ is None:
                public_root = self.public_orthanc_root_

                studyIds = ",".join([s.orthanc_id for s in request.resources])
                return urllib.parse.urljoin(public_root, f"osimis-viewer/app/index.html?pickableStudyIds={studyIds}&selectedStudyIds={studyIds}&token={token}")
            else:
                return urllib.parse.urljoin(self.public_landing_root_, f"?token={token}")

        elif request.type == TokenType.STONE_VIEWER_PUBLICATION:
            if not has_dicom_uids:
                logging.error("No dicom_uid provided while generating a link to the StoneViewer")
                return None

            if skip_landing_page or self.public_landing_root_ is None:
                public_root = self.public_orthanc_root_

                studyIds = ",".join([s.dicom_uid for s in request.resources])
                return urllib.parse.urljoin(public_root, f"stone-webviewer/index.html?study={studyIds}&selectedStudies={studyIds}&token={token}")
            else:
                return urllib.parse.urljoin(self.public_landing_root_, f"?token={token}")

        elif request.type == TokenType.OHIF_VIEWER_PUBLICATION:

            if self.ohif_data_source_ == "dicom-json":
                if not has_orthanc_ids:
                    logging.error("No orthanc_id provided while generating a link to the OHIF viewer in 'dicom-json' data source mode")
                    return None
                studyIds = ",".join([s.orthanc_id for s in request.resources])
                ohif_url_format = f"viewer?url=../studies/{studyIds}/ohif-dicom-json&token={token}"
            elif self.ohif_data_source_ == "dicom-web":
                if not has_dicom_uids:
                    logging.error("No dicom_uid provided while generating a link to the OHIF viewer in 'dicom-web' data source mode")
                    return None
                studyIds = ",".join([s.dicom_uid for s in request.resources])
                ohif_url_format = f"viewer?StudyInstanceUIDs={studyIds}&token={token}"
            else:
                logging.error(f"Unsupported OHIF data source: {self.ohif_data_source_}")
                return None


            if skip_landing_page or self.public_landing_root_ is None:
                public_root = self.public_ohif_root_
                return urllib.parse.urljoin(public_root, ohif_url_format)
            else:
                return urllib.parse.urljoin(self.public_landing_root_, f"?token={token}")

        elif request.type == TokenType.VOLVIEW_VIEWER_PUBLICATION:

            if not has_orthanc_ids:
                logging.error("No orthanc_id provided while generating a link to the VolView viewer")
                return None
            study_ids_url = ",".join(["../studies/"+s.orthanc_id+"/archive" for s in request.resources])
            volview_url_format = f"volview/index.html?names=[archive.zip]&urls={study_ids_url}&token={token}"

            if skip_landing_page or self.public_landing_root_ is None:
                public_root = self.public_orthanc_root_
                return urllib.parse.urljoin(public_root, volview_url_format)
            else:
                return urllib.parse.urljoin(self.public_landing_root_, f"?token={token}")

        elif request.type == TokenType.MEDDREAM_INSTANT_LINK:
            if not has_dicom_uids:
                logging.error("No dicom_uid provided while generating a link to the MedDream Viewer")
                return None

            studyIds = ",".join([s.dicom_uid for s in request.resources])
            logging.warning("generateUrl meddream instant " + self.public_meddream_root_)
            return urllib.parse.urljoin(self.public_meddream_root_, f"?study={studyIds}&token={token}")

        elif request.type == TokenType.MEDDREAM_VIEWER_PUBLICATION:
            logging.warning("generateUrl meddream publication " + self.public_meddream_root_)
            return urllib.parse.urljoin(self.public_landing_root_, f"?token={token}")

        elif request.type in [
            TokenType.VIEWER_INSTANT_LINK,
            TokenType.DOWNLOAD_INSTANT_LINK
            ]:
            # no url, the user must build it himself
            return None

    def check_token_is_allowed(self, type: TokenType):
        if type in [TokenType.OSIMIS_VIEWER_PUBLICATION, TokenType.STONE_VIEWER_PUBLICATION, TokenType.VOLVIEW_VIEWER_PUBLICATION]:
            if self.public_orthanc_root_ is None:
                raise SharesException(f"'{type}' are disabled")

        elif type == TokenType.OHIF_VIEWER_PUBLICATION and self.public_ohif_root_ is None:
            raise SharesException(f"'{type}' are disabled")

        elif type == TokenType.MEDDREAM_INSTANT_LINK and self.meddream_token_service_url_ is None:
            raise SharesException(f"'{type}' are disabled")

        elif type == TokenType.MEDDREAM_VIEWER_PUBLICATION and self.public_landing_root_ is None:
            raise SharesException(f"'{type}' are disabled")

        # no restrictions for others, the user must build the url himself

    def is_expired(self, token_request: TokenCreationRequest) -> bool:
        return self.tokens_manager_.is_expired(token_request)


    def is_valid(self, token: str, orthanc_id: Optional[str], dicom_uid: Optional[str], server_id: Optional[str]) -> bool:
        return self.tokens_manager_.is_valid(
            token=token,
            orthanc_id=orthanc_id,
            dicom_uid=dicom_uid,
            server_id=server_id
        )

    def create_token(self, request: TokenCreationRequest):
        logging.info("creating token: " + request.json())

        self.check_token_is_allowed(type=request.type)

        if request.type in [
            TokenType.OSIMIS_VIEWER_PUBLICATION,
            TokenType.STONE_VIEWER_PUBLICATION,
            TokenType.OHIF_VIEWER_PUBLICATION,
            TokenType.DOWNLOAD_INSTANT_LINK,
            TokenType.VIEWER_INSTANT_LINK,
            TokenType.VOLVIEW_VIEWER_PUBLICATION
        ]:
            token = self.tokens_manager_.generate_token(request=request)

        elif request.type == TokenType.MEDDREAM_INSTANT_LINK:
            # for the instant link, we get the token directly from the meddream token service
            items = []
            for resource in request.resources:
                if resource.level != Levels.STUDY:
                    logging.error(f"'{request.type}': Not a study")
                    return None

                items.append({
                        "studies" : {
                            "study": resource.dicom_uid,
                            "storage": "Orthanc"
                        }
                    })

            token = httpx.post(self.meddream_token_service_url_, json={
                "items": items
            }).text

        elif request.type == TokenType.MEDDREAM_VIEWER_PUBLICATION:
            # we do not generate a meddream token now, this will be handled by the meddread-share-redirect service at the time we try to access the link
            has_dicom_uids = all([s.dicom_uid is not None for s in request.resources])

            if not has_dicom_uids:
                raise SharesException("No dicom_uid provided while generating a link to the MedDream Viewer")

            token = self.tokens_manager_.generate_token(request=request)

        response = TokenCreationResponse(
            request=request,
            token=token,
            url=self._generate_url(
                request=request,
                token=token
            )
        )
        logging.info("created token: " + response.json())
        return response

    def decode_token(self, token: str) -> TokenDecoderResponse:
        try:
            if token.startswith("Bearer "):
                token = token.replace("Bearer ", "")

            logging.info("Decode token: " + token)

            response = TokenDecoderResponse(resources=[])

            # try to decode the token to get the token_creation_request
            token_creation_request = TokenCreationRequest(**self.tokens_manager_._decode_token(token))  # this will raise if the token can not be decoded
            response.token_type = token_creation_request.type

            if self.is_expired(token_creation_request):
                response.error_code = DecoderErrorCodes.EXPIRED
                return response

            # we can not check that the token is valid for the given study, this will be checked by the auth plugin once the viewer opens
            response.redirect_url = self.redirect_to_viewer(token=token)
            response.resources = token_creation_request.resources

            return response

        except InvalidTokenException as ex:
            logging.exception(ex)
            response.error_code = DecoderErrorCodes.INVALID
            return response

        except SharesException as ex:
            logging.exception(ex)
            response.error_code = DecoderErrorCodes.UNKNOWN
            return response

        except Exception as ex:
            logging.exception(ex)
            response.error_code = DecoderErrorCodes.UNKNOWN
            return response

    def get_request_from_token(self, token: str) -> TokenCreationRequest:
        return self.tokens_manager_.get_request_from_token(token=token)

    def redirect_to_viewer(self, token: str = None) -> str:

        logging.warning("redirecting to viewer: " + token)

        # extract the initial share request from the token
        request = self.tokens_manager_.get_request_from_token(token=token)

        if request.type in [TokenType.OSIMIS_VIEWER_PUBLICATION, TokenType.STONE_VIEWER_PUBLICATION, TokenType.OHIF_VIEWER_PUBLICATION, TokenType.VOLVIEW_VIEWER_PUBLICATION]:

            # check it is valid (this actually only checks the expiration date since we get the ids from the request itself !)
            if not self.is_expired(request):
                return self._generate_url(
                    request=request,
                    token=token,
                    skip_landing_page=True  # this time, we want a direct link to the viewer
                )

        elif request.type == TokenType.MEDDREAM_VIEWER_PUBLICATION:

            # check it is valid (this actually only checks the expiration date since we get the ids from the request itself !)
            if not self.is_expired(request):
                # generate a new meddream token that will be valid for only a few minutes
                request.type = TokenType.MEDDREAM_INSTANT_LINK
                new_token = self.create_token(request)
                return new_token.url

        raise SharesException("Token is not valid")
