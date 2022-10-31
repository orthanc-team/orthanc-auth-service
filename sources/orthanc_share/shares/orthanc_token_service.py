from .tokens_manager import Hs256TokensManager, TokensManager
from .models import *
import urllib
import httpx
from typing import Optional
from .exceptions import *



class OrthancTokenService:

    tokens_manager_: TokensManager = None

    secret_key_: str

    public_orthanc_root_: Optional[str] = None
    standard_server_identifier_: Optional[str] = None
    public_anonymized_orthanc_root_: Optional[str] = None
    anonymized_server_identifier_: Optional[str] = None

    meddream_token_service_url_: Optional[str] = None
    public_meddream_root_: Optional[str] = None
    public_landing_root_: Optional[str] = None

    def __init__(self, secret_key: str):
        self.secret_key_ = secret_key

    def _configure_server(self, public_orthanc_root: str, server_identifier: Optional[str] = None, public_landing_root: Optional[str] = None):
        self.public_orthanc_root_ = public_orthanc_root
        self.server_identifier_ = server_identifier
        self.public_landing_root_ = public_landing_root

    def _configure_anonymized_server(self, public_anonymized_orthanc_root: str, anonymized_server_identifier: Optional[str] = None):
        self.public_anonymized_orthanc_root_ = public_anonymized_orthanc_root
        self.anonymized_server_identifier_ = anonymized_server_identifier

    def _configure_meddream(self, meddream_token_service_url: str, public_meddream_root: str, public_landing_root: str):
        self.meddream_token_service_url_ = meddream_token_service_url
        self.public_meddream_root_ = public_meddream_root
        self.public_landing_root_ = public_landing_root

    def _create(self):
        if not self.tokens_manager_:
            self.tokens_manager_ = Hs256TokensManager(
                secret_key=self.secret_key_,
                standard_server_identifier=self.standard_server_identifier_,
                anonymized_server_identifier=self.anonymized_server_identifier_
            )
        return self.tokens_manager_


    def _generate_url(self, share_request: ShareRequest, token: str, skip_landing_page: bool = False):

        share_request_has_dicom_uids = all([s.dicom_uid is not None for s in share_request.studies])
        share_request_has_orthanc_ids = all([s.orthanc_id is not None for s in share_request.studies])

        if share_request.type == ShareType.osimis_viewer_publication:
            if not share_request_has_orthanc_ids:
                logging.error("No orthanc_id provided while generating a link to the Osimis WebViewer")
                return None

            if skip_landing_page or self.public_landing_root_ is None:
                if share_request.anonymized:
                    public_root = self.public_anonymized_orthanc_root_
                else:
                    public_root = self.public_orthanc_root_
                return urllib.parse.urljoin(public_root, f"osimis-viewer/app/index.html?study={share_request.orthanc_id}&token={token}")
            else:
                return urllib.parse.urljoin(self.public_orthanc_root_, f"/welcome/?token={token}")

        elif share_request.type == ShareType.meddream_instant_link:
            if not share_request_has_dicom_uids:
                logging.error("No dicom_uid provided while generating a link to the MedDream Viewer")
                return None

            logging.warning("generateUrl meddream instant " + self.public_meddream_root_)
            return urllib.parse.urljoin(self.public_meddream_root_, f"?token={token}")

        elif share_request.type == ShareType.meddream_viewer_publication:
            logging.warning("generateUrl meddream publication " + self.public_meddream_root_)
            return urllib.parse.urljoin(self.public_landing_root_, f"?token={token}")

    def check_share_is_allowed(self, type: ShareType, is_anonymized: bool):
        if type == ShareType.osimis_viewer_publication:
            if is_anonymized and self.public_anonymized_orthanc_root_ is None:
                raise SharesException("Anonymized 'osimis-viewer-publication' are disabled")
            elif not is_anonymized and self.public_orthanc_root_ is None:
                raise SharesException("Standard 'osimis-viewer-publication' are disabled")

        elif is_anonymized and type in [ShareType.meddream_instant_link, ShareType.meddream_viewer_publication]:
            raise SharesException("Anonymized shares are not available with MedDream")

        elif type == ShareType.meddream_instant_link and self.meddream_token_service_url_ is None:
            raise SharesException("'meddream-instant-link' are disabled")

        elif type == ShareType.meddream_viewer_publication and self.public_landing_root_ is None:
            raise SharesException("'meddream-viewer-publication' are disabled")

    def is_expired(self, share_request: ShareRequest) -> bool:
        return self.tokens_manager_.is_expired(share_request)


    def is_valid(self, token: str, orthanc_id: Optional[str], dicom_uid: Optional[str], server_identifier: Optional[str]) -> bool:
        return self.tokens_manager_.is_valid(
            token=token,
            orthanc_id=orthanc_id,
            dicom_uid=dicom_uid,
            server_identifier=server_identifier
        )

    def create_share(self, share_request: ShareRequest):
        logging.info("creating share: " + share_request.json())

        self.check_share_is_allowed(type=share_request.type, is_anonymized=share_request.anonymized)

        if share_request.type == ShareType.osimis_viewer_publication:
            token = self.tokens_manager_.generate_token(share_request=share_request)

        elif share_request.type == ShareType.meddream_instant_link:
            # for the instant link, we get the token directly from the meddream token service
            items = []
            for study in share_request.studies:
                items.append({
                        "studies" : {
                            "study": study.dicom_uid,
                            "storage": "Orthanc"
                        }
                    })

            token = httpx.post(self.meddream_token_service_url_, json={
                "items": items
            }).text

        elif share_request.type == ShareType.meddream_viewer_publication:
            # we do not generate a meddream token now, this will be handled by the meddread-share-redirect service at the time we try to access the link
            share_request_has_dicom_uids = all([s.dicom_uid is not None for s in share_request.studies])

            if not share_request_has_dicom_uids:
                raise SharesException("No dicom_uid provided while generating a link to the MedDream Viewer")

            token = self.tokens_manager_.generate_token(share_request=share_request)

        share = Share(
            request=share_request,
            token=token,
            url=self._generate_url(
                share_request=share_request,
                token=token
            )
        )
        logging.info("created share: " + share.json())
        return share


    def get_share_request_from_token(self, token: str) -> ShareRequest:
        return self.tokens_manager_.get_share_request_from_token(token=token)


    def redirect_to_viewer(self, token: str = None) -> str:

        logging.warning("redirecting to viewer: " + token)

        # extract the initial share request from the token
        share_request = self.tokens_manager_.get_share_request_from_token(token=token)

        if share_request.type == ShareType.osimis_viewer_publication:

            # check it is valid (this actually only checks the expiration date since we get the ids from the request itself !)
            if not self.is_expired(share_request):
                return self._generate_url(
                    share_request=share_request,
                    token=token,
                    skip_landing_page=True  # this time, we want a direct link to the viewer
                )

        elif share_request.type == ShareType.meddream_viewer_publication:

            # check it is valid (this actually only checks the expiration date since we get the ids from the request itself !)
            if not self.is_expired(share_request):
                # generate a new meddream token that will be valid for only a few minutes
                share_request.type = ShareType.meddream_instant_link
                share = self.create_share(share_request)
                return share.url

        raise SharesException("Token is not valid")
