# SPDX-FileCopyrightText: 2022 - 2023 Orthanc Team SRL <info@orthanc.team>
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
        server_id = None

        if not is_secret_defined("SERVER_ID"):
            logging.warning("SERVER_ID is not defined.  This is not mandatory")
        else:
            server_id = get_secret_or_die("SERVER_ID")

        if not is_secret_defined("PUBLIC_LANDING_ROOT"):
            logging.warning("PUBLIC_LANDING_ROOT is not defined.  Users won't get a clear error message if their link is invalid or expired")
        else:
            public_landing_root = get_secret_or_die("PUBLIC_LANDING_ROOT")

        token_service._configure_server(
            public_orthanc_root=public_orthanc_root,
            server_id=server_id,
            public_landing_root=public_landing_root
        )
    else:
        logging.warning("PUBLIC_ORTHANC_ROOT is not defined, the generator will not allow 'osimis-viewer-publication' or 'stone-viewer-publication' shares")

    if is_secret_defined("PUBLIC_OHIF_ROOT"):
        logging.warning("PUBLIC_OHIF_ROOT is defined, configuring generator for standard 'ohif-viewer-publication'")
        public_ohif_root = get_secret_or_die("PUBLIC_OHIF_ROOT")
        server_id = None

        if not is_secret_defined("SERVER_ID"):
            logging.warning("SERVER_ID is not defined.  This is not mandatory")
        else:
            server_id = get_secret_or_die("SERVER_ID")

        if not is_secret_defined("OHIF_DATA_SOURCE"):
            logging.warning("OHIF_DATA_SOURCE is not defined, will default to dicom-json.")
            ohif_data_source = "dicom-json"
        else:
            ohif_data_source = get_secret_or_die("OHIF_DATA_SOURCE")
            if ohif_data_source == "dicom-web":
                logging.warning("OHIF_DATA_SOURCE is defined - using dicom-web")
            elif ohif_data_source == "dicom-json":
                logging.warning("OHIF_DATA_SOURCE is defined - using dicom-json")
            else:
                logging.warning("Invalid OHIF_DATA_SOURCE value. It should be either 'dicom-json' or 'dicom-web'.")
                ohif_data_source = "dicom-json"  # Default to dicom-json for unexpected values

        if not is_secret_defined("PUBLIC_LANDING_ROOT"):
            logging.warning("PUBLIC_LANDING_ROOT is not defined.  Users won't get a clear error message if their link is invalid or expired")
        else:
            public_landing_root = get_secret_or_die("PUBLIC_LANDING_ROOT")

        token_service._configure_ohif(
            public_ohif_root=public_ohif_root,
            server_id=server_id,
            public_landing_root=public_landing_root,
            ohif_data_source=ohif_data_source
        )
    else:
        logging.warning("PUBLIC_OHIF_ROOT is not defined, the generator will not allow 'ohif-viewer-publication'")

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

    if is_secret_defined("SHLINK_ENABLED") and get_secret_or_die("SHLINK_ENABLED").lower() == "true":
        logging.warning("SHLINK_ENABLED is set, will shorten publication URLs.")
        shlink_api_key = None
        shlink_base_url = None

        if is_secret_defined("SHLINK_API_KEY"):
            shlink_api_key = get_secret_or_die("SHLINK_API_KEY")
        else:
            logging.warning("SHLINK_ENABLED is set to true, but SHLINK_API_KEY is not defined. Shlink will not be fully functional.")

        if is_secret_defined("SHLINK_BASE_URL"):
            shlink_base_url = get_secret_or_die("SHLINK_BASE_URL")
        else:
            logging.warning("SHLINK_ENABLED is set to true, but SHLINK_BASE_URL is not defined. Shlink will not be fully functional.")

        token_service._configure_shlink(
            shlink_api_key=shlink_api_key,
            shlink_base_url=shlink_base_url
        )
    else:
        logging.info("Shlink URL shortener is not enabled.")

    token_service._create()
    return token_service
