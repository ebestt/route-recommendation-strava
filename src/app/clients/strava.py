from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import requests

BASE_URL = "https://www.strava.com/api/v3"
OAUTH_URL = "https://www.strava.com/oauth"


@dataclass
class StravaConfig:
    client_id: str
    client_secret: str
    redirect_uri: str


class StravaClient:
    def __init__(self, config: StravaConfig):
        self.config = config

    @staticmethod
    def from_env() -> "StravaClient":
        return StravaClient(
            StravaConfig(
                client_id=os.getenv("STRAVA_CLIENT_ID", ""),
                client_secret=os.getenv("STRAVA_CLIENT_SECRET", ""),
                redirect_uri=os.getenv(
                    "STRAVA_REDIRECT_URI", "http://localhost:8000/auth/callback"
                ),
            )
        )

    def authorize_url(self) -> str:
        return (
            f"{OAUTH_URL}/authorize?client_id={self.config.client_id}"
            f"&response_type=code&redirect_uri={self.config.redirect_uri}"
            "&approval_prompt=auto&scope=read,activity:read_all"
        )

    def exchange_code(self, code: str) -> dict[str, Any]:
        response = requests.post(
            f"{OAUTH_URL}/token",
            data={
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret,
                "code": code,
                "grant_type": "authorization_code",
            },
            timeout=20,
        )
        response.raise_for_status()
        return response.json()

    def refresh_access_token(self, refresh_token: str) -> dict[str, Any]:
        response = requests.post(
            f"{OAUTH_URL}/token",
            data={
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
            timeout=20,
        )
        response.raise_for_status()
        return response.json()

    def get_athlete_activities(self, access_token: str, per_page: int = 100) -> list[dict[str, Any]]:
        page = 1
        activities: list[dict[str, Any]] = []
        while True:
            response = requests.get(
                f"{BASE_URL}/athlete/activities",
                headers={"Authorization": f"Bearer {access_token}"},
                params={"per_page": per_page, "page": page},
                timeout=30,
            )
            response.raise_for_status()
            page_results = response.json()
            if not page_results:
                break
            activities.extend(page_results)
            page += 1
            if len(page_results) < per_page:
                break
        return activities
