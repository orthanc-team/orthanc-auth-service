import httpx
import logging
from dataclasses import dataclass, asdict, field
from typing import Optional, List, Dict
from datetime import datetime

logging.basicConfig(level=logging.INFO)

SHLINK_URL_ENDPOINT = "/rest/v3/short-urls"

@dataclass
class ShortenURLParameters:
    longUrl: str
    deviceLongUrls: Optional[Dict[str, str]] = None
    validSince: Optional[datetime] = None
    validUntil: Optional[datetime] = None
    maxVisits: Optional[int] = None
    tags: List[str] = field(default_factory=list)
    title: Optional[str] = None
    crawlable: Optional[bool] = None
    forwardQuery: Optional[bool] = None
    customSlug: Optional[str] = None
    findIfExists: Optional[bool] = None
    domain: Optional[str] = None
    shortCodeLength: Optional[int] = None

class Shlink:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "X-Api-Key": self.api_key,
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    def shorten_url(self, params: ShortenURLParameters) -> Optional[str]:
        """Shorten a given URL using Shlink. Return the shortened URL or None if there is an error."""
        endpoint_url = f"{self.base_url}{SHLINK_URL_ENDPOINT}"
        payload = asdict(params)
        if payload.get('validSince'):
            payload['validSince'] = payload['validSince'].isoformat()
        if payload.get('validUntil'):
            payload['validUntil'] = payload['validUntil'].isoformat()

        # Remove fields with None values from the payload
        payload = {k: v for k, v in payload.items() if v is not None}

        try:
            response = httpx.post(endpoint_url, headers=self.headers, json=payload, timeout=10)

            if not response.is_error:
                data = response.json()
                short_code = data.get("shortCode")
                if short_code:
                    return f"{self.base_url}/{short_code}"
                logging.error(f"Shlink response does not contain a shortCode: {response.text}")
            else:
                logging.error(f"Error shortening URL with Shlink. Status Code: {response.status_code}. Response: {response.text}")

        except httpx.RequestError as exc:
            logging.error(f"Request error encountered while shortening URL with Shlink: {exc}")
        except Exception as exc:
            logging.error(f"Unexpected error while shortening URL with Shlink: {exc}")

        return None
