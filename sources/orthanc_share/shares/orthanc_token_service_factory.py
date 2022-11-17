# SPDX-FileCopyrightText: 2022 Orthanc Team SRL <info@orthanc.team>
#
# SPDX-License-Identifier: GPL-3.0-or-later

from .orthanc_token_service import OrthancTokenService
from .utils.utils import get_secret_or_die, is_secret_defined

import os
import logging

def create_token_service_from_secrets():

    token_service = OrthancTokenService(
        secret_key=get_secret_or_die("SECRET_KEY")
    )

    public_landing_root = None

    if is_secret_defined("PUBLIC_ORTHANC_ROOT"):
        logging.warning("PUBLIC_ORTHANC_ROOT is defined, configuring generator for standard 'osimis-viewer-publication' and 'stone-viewer-publication' shares")
        public_orthanc_root = get_secret_or_die("PUBLIC_ORTHANC_ROOT")
        server_identifier = None

        if not is_secret_defined("SERVER_IDENTIFIER"):
            logging.warning("SERVER_IDENTIFIER is not defined.  This is fine if you do not enable anonymized shares")
        else:
            server_identifier = get_secret_or_die("SERVER_IDENTIFIER")

        if not is_secret_defined("PUBLIC_LANDING_ROOT"):
            logging.warning("PUBLIC_LANDING_ROOT is not defined.  Users won't get a clear error message if their link is invalid or expired")
        else:
            public_landing_root = get_secret_or_die("PUBLIC_LANDING_ROOT")

        token_service._configure_server(
            public_orthanc_root=public_orthanc_root,
            server_identifier=server_identifier,
            public_landing_root=public_landing_root
        )
    else:
        logging.warning("PUBLIC_ORTHANC_ROOT is not defined, the generator will not allow 'osimis-viewer-publication' or 'stone-viewer-publication' shares")

    if is_secret_defined("PUBLIC_ANONYMIZED_ORTHANC_ROOT"):
        logging.warning("PUBLIC_ANONYMIZED_ORTHANC_ROOT is defined, configuring generator for anonymized 'osimis-viewer-publication' shares")
        public_anonymized_orthanc_root = get_secret_or_die("PUBLIC_ANONYMIZED_ORTHANC_ROOT")
        anonymized_server_identifier = None

        if not is_secret_defined("ANONYMIZED_SERVER_IDENTIFIER"):
            logging.warning("ANONYMIZED_SERVER_IDENTIFIER is not defined.  This is fine if you do not enable standard shares")
        else:
            anonymized_server_identifier = get_secret_or_die("ANONYMIZED_SERVER_IDENTIFIER")

        token_service._configure_anonymized_server(
            public_anonymized_orthanc_root=public_anonymized_orthanc_root,
            anonymized_server_identifier=anonymized_server_identifier
        )
    else:
        logging.warning("PUBLIC_ANONYMIZED_ORTHANC_ROOT is not defined, the generator will not allow anonymized 'osimis-viewer-publication' shares")

    if is_secret_defined("MEDDREAM_TOKEN_SERVICE_URL") and is_secret_defined("PUBLIC_MEDDREAM_ROOT"):
        logging.warning("MEDDREAM_TOKEN_SERVICE_URL and PUBLIC_MEDDREAM_ROOT are defined, configuring generator for 'meddream-instant-links' shares")
        meddream_token_service_url = get_secret_or_die("MEDDREAM_TOKEN_SERVICE_URL")
        public_meddream_root = get_secret_or_die("PUBLIC_MEDDREAM_ROOT")

        if not public_meddream_root.endswith('/'):
            logging.error("PUBLIC_MEDDREAM_ROOT should end with a '/'")
            exit(-1)

        if is_secret_defined("PUBLIC_LANDING_ROOT"):
            logging.warning("PUBLIC_LANDING_ROOT is defined, configuring generator for 'meddream-viewer-publication' shares")
            public_landing_root = get_secret_or_die("PUBLIC_LANDING_ROOT")
        else:
            logging.warning("PUBLIC_LANDING_ROOT is not defined, the generator will not allow 'meddream-viewer-publication' shares")

        token_service._configure_meddream(
            meddream_token_service_url=meddream_token_service_url,
            public_meddream_root=public_meddream_root,
            public_landing_root=public_landing_root
        )
    else:
        logging.warning("MEDDREAM_TOKEN_SERVICE_URL or PUBLIC_MEDDREAM_ROOT are not defined, the generator will not allow 'meddream-instant-links' shares")

    token_service._create()
    return token_service