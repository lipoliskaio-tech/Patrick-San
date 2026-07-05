"""
Cliente HTTP para comunicação com a API de licenciamento.
"""
from typing import Optional

import requests

from hwid import get_hwid

# Ajuste para a URL real da sua API em produção.
API_BASE_URL = "http://localhost:8000"
CURRENT_VERSION = "1.0.0"
REQUEST_TIMEOUT = 10


class LicenseClient:
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.session_token: Optional[str] = None

    def check_maintenance(self) -> dict:
        response = requests.get(f"{self.base_url}/client/maintenance", timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()

    def login(self, license_key: str) -> dict:
        hwid = get_hwid()
        payload = {
            "license_key": license_key.strip(),
            "hwid": hwid,
            "version": CURRENT_VERSION,
        }
        response = requests.post(
            f"{self.base_url}/client/login", json=payload, timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()
        if data.get("success") and data.get("session_token"):
            self.session_token = data["session_token"]
        return data

    def send_heartbeat(self) -> bool:
        if not self.session_token:
            return False
        try:
            response = requests.post(
                f"{self.base_url}/client/heartbeat",
                json={"session_token": self.session_token},
                timeout=REQUEST_TIMEOUT,
            )
            return response.status_code == 200
        except requests.RequestException:
            return False

    def check_update(self) -> dict:
        response = requests.get(
            f"{self.base_url}/client/version/check",
            params={"current_version": CURRENT_VERSION},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()

    def get_history(self, license_key: str) -> list:
        response = requests.get(
            f"{self.base_url}/client/history/{license_key}", timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        return response.json()
