from pydantic import BaseModel, Field
import requests
from typing import Type
from .auth import AmadeusAuth
from langchain.tools import BaseTool


class ActivitySearchInput(BaseModel):
    """Input schema for activity search"""

    location: str = Field(
        description="The city name to search for activities (e.g., 'Paris', 'New York')"
    )
    radius: int = Field(5, description="Search radius in kilometers (default: 5)")


class ActivitySearchTool(BaseTool):
    """Tool for searching tours and activities using Amadeus Shopping API"""

    name: str = "get_place_details"  # Keeping your original name for compatibility
    description: str = """
    Searches for top-rated tours, museums, and activities in a specific city.
    Returns details including name, price, booking link, and short description.
    Input should be the city name (e.g. 'Paris').
    """
    args_schema: Type[BaseModel] = ActivitySearchInput
    amadeus_auth: AmadeusAuth = None

    def __init__(self, amadeus_auth: AmadeusAuth):
        super().__init__()
        self.amadeus_auth = amadeus_auth

    def _get_coordinates(self, token: str, keyword: str) -> tuple[float, float] | None:
        """Helper to convert city name to Lat/Lon"""
        url = f"{self.amadeus_auth.base_url}/v1/reference-data/locations"
        headers = {"Authorization": f"Bearer {token}"}
        params = {"keyword": keyword, "subType": "CITY", "page[limit]": 1}

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            if data.get("data"):
                geo = data["data"][0]["geoCode"]
                print(
                    f"Found coordinates for {keyword}: {geo['latitude']}, {geo['longitude']}"
                )
                return geo["latitude"], geo["longitude"]
            print(f"No location found for keyword: {keyword}")
            return None
        except Exception as e:
            print(f"Error getting coordinates: {str(e)}")
            return None

    def _run(self, location: str, radius: int = 5) -> str:
        """Search for activities"""
        try:
            token = self.amadeus_auth.get_access_token()

            coords = self._get_coordinates(token, location)
            if not coords:
                return f"Could not find coordinates for location: {location}"

            lat, lon = coords

            url = f"{self.amadeus_auth.base_url}/v1/shopping/activities"
            headers = {"Authorization": f"Bearer {token}"}
            params = {"latitude": lat, "longitude": lon, "radius": radius}

            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            if not data.get("data"):
                return f"No activities found in {location}."

            results = []
            for item in data["data"][:5]:
                name = item.get("name", "Unknown Activity")
                booking_link = item.get("bookingLink", "N/A")

                # Price formatting
                price_data = item.get("price", {})
                amount = price_data.get("amount", "N/A")
                currency = price_data.get("currencyCode", "")
                price_str = (
                    f"{amount} {currency}" if amount != "N/A" else "Price not available"
                )

                # Description parsing
                short_desc = item.get("shortDescription", "No description")

                # Format output
                entry = (
                    f"Activity: {name}\n"
                    f"Price: {price_str}\n"
                    f"Description: {short_desc}\n"
                    f"Link: {booking_link}\n"
                )
                results.append(entry)

            return "\n---\n".join(results)

        except requests.exceptions.HTTPError as e:
            return f"Amadeus API Error: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return f"Error searching activities: {str(e)}"

    async def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async not supported yet")
