from langchain.tools import tool
from langsmith import traceable
import requests
from typing import Optional


@tool
@traceable(run_type="tool", name="get_user_location")
def get_user_location(ip_address: Optional[str] = None) -> str:
    """
    Identifies the city and country of a user based on their IP address.
    If no IP is provided, it detects the current machine's public IP.
    """
    try:
        # If no IP is passed, the API automatically sees the caller's public IP
        # Note: If deployed on a server, this finds the server's location unless 'ip_address' is provided!
        url = (
            f"http://ip-api.com/json/{ip_address}"
            if ip_address
            else "http://ip-api.com/json/"
        )

        response = requests.get(url, timeout=5)
        data = response.json()

        if data["status"] == "fail":
            return f"Error locating user: {data['message']}"

        city = data.get("city", "Unknown City")
        country = data.get("country", "Unknown Country")
        region = data.get("regionName", "")

        return f"{city}, {region}, {country}"

    except Exception as e:
        return f"Failed to retrieve location. Error: {str(e)}"


# Example Usage:
# print(get_user_location())              # Finds YOUR location (if running locally)
# print(get_user_location("24.48.0.1"))   # Finds location of this specific IP

