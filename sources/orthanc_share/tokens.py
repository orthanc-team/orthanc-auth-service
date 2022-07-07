from models import *


class TokensManager:

    def _encode_token(self, share_request: ShareRequest) -> str:
        return None # to override in derived class

    def _decode_token(self, token) -> dict:
        return None # to override in derived class

    def generate_token(self, share_request: ShareRequest) -> str:
        return self._encode_token(share_request)

    def is_valid(self, token: str, orthanc_id: str = None, dicom_uid: str = None) -> bool:

        # no ids to check, we consider it's invalid
        if not dicom_uid and not orthanc_id:
            return False

        try:
            r = self._decode_token(token)
            share_request = ShareRequest(**r)
        except:
            return False

        granted = True

        # check the ids.  The share_request might have been generated with 2 ids
        # but when we check, we'll probably only have a single ID
        if dicom_uid:
            granted = granted and (share_request.dicom_uid == dicom_uid)

        if orthanc_id:
            granted = granted and (share_request.orthanc_id == orthanc_id)

        # check expiration date
        if share_request.expiration_date:
            expiration_date = parser.parse(share_request.expiration_date)
            now_utc = pytz.UTC.localize(datetime.now())

            granted = granted and (now_utc < expiration_date)

        return granted



class Hs256TokensManager(TokensManager):

    secret_key: str

    def __init__(self, secret_key: str):
        self.secret_key = secret_key

    def _encode_token(self, share_request: ShareRequest) -> str:
        return jwt.encode(share_request.dict(), self.secret_key, algorithm="HS256")

    def _decode_token(self, token: str) -> dict:
        return jwt.decode(token, self.secret_key, algorithms="HS256")

