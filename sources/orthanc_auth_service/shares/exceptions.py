# SPDX-FileCopyrightText: 2022 - 2023 Orthanc Team SRL <info@orthanc.team>
#
# SPDX-License-Identifier: GPL-3.0-or-later

class SharesException(Exception):

    def __init__(self, msg="Unknown Shares exception"):
        self.msg = msg

    def __str__(self):
        return self.msg


class InvalidTokenException(SharesException):

    def __init__(self):
        super().__init__(msg="Invalid token")


class ShlinkException(Exception):
    def __init__(self, msg="Error related to Shlink (URL Shortener)"):
        self.msg = msg

    def __str__(self):
        return self.msg
