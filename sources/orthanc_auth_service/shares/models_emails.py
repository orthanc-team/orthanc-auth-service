# SPDX-FileCopyrightText: 2022 - 2025 Orthanc Team SRL <info@orthanc.team>
#
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Optional
from pydantic import BaseModel, Field


class SendEmailRequest(BaseModel):
    destination_email: Optional[str] = Field(alias="destination-email", default=None)
    email_title: Optional[str] = Field(alias="email-title", default=None)
    email_content: Optional[str] = Field(alias="email-content", default=None)
    layout_template: Optional[str] = Field(alias="layout-template", default=None)

    class Config:  # allow creating object from dict (used when deserializing the JWT)
        populate_by_name = True


class SendEmailResponse(BaseModel):
    success: bool
    details: Optional[str] = None
