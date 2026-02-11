# SPDX-FileCopyrightText: 2022 - 2026 Orthanc Team SRL <info@orthanc.team>
#
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import logging
import datetime
from json import JSONEncoder

# try to read a secret first from a secret file or from an env var.
# stop execution if not
def get_secret_or_die(name: str) -> str:
    secret_file_path = f"/run/secrets/{name}"
    if os.path.exists(secret_file_path) and os.path.isfile(secret_file_path):
        with open(secret_file_path, "rt") as secret_file:
            return secret_file.read().strip()

    if os.environ.get(name) is not None:
        return os.environ.get(name)

    logging.error(f"Secret '{name}' is not defined, can not start without it")
    exit(-1)


def is_secret_defined(name: str) -> bool:

    secret_file_path = f"/run/secrets/{name}"
    if os.path.exists(secret_file_path) and os.path.isfile(secret_file_path):
        return True

    return os.environ.get(name) is not None


class DateTimeJSONEncoder(JSONEncoder):
    # Override the default method
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()