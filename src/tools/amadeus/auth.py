import requests
from datetime import datetime


class AmadeusAuth:
    """Handle Amadeus API authentication"""

    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://test.api.amadeus.com"
        self.access_token = None
        self.token_expires_at = None

    def get_access_token(self) -> str | None:
        """Get or refresh access token"""
        if self.access_token and self.token_expires_at:
            if datetime.now().timestamp() < self.token_expires_at:
                return self.access_token

        url = f"{self.base_url}/v1/security/oauth2/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.api_secret,
        }

        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()

        token_data = response.json()
        self.access_token = token_data["access_token"]
        self.token_expires_at = datetime.now().timestamp() + token_data["expires_in"]

        return self.access_token
