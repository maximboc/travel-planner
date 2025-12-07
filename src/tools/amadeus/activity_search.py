from pydantic import BaseModel, Field
import requests
from typing import Dict, List, Type
from .auth import AmadeusAuth
from langchain.tools import BaseTool

from src.states import ActivityResultState


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
    amadeus_auth: AmadeusAuth | None = None

    def __init__(self, amadeus_auth: AmadeusAuth | None = None):
        super().__init__()
        self.amadeus_auth = amadeus_auth

    def _get_coordinates(self, token: str, keyword: str) -> tuple[float, float] | None:
        """Helper to convert city name to Lat/Lon"""
        if not self.amadeus_auth:
            return None

        url: str = f"{self.amadeus_auth.base_url}/v1/reference-data/locations"
        headers: Dict[str, str] = {"Authorization": f"Bearer {token}"}
        params: Dict[str, str | int] = {
            "keyword": keyword,
            "subType": "CITY,AIRPORT",
            "page[limit]": 1,
        }

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

    def _run(
        self, location: str, radius: int = 5, max_places: int = 5
    ) -> List[ActivityResultState]:
        """Search for activities"""
        if not self.amadeus_auth:
            raise ValueError("AmadeusAuth instance is required for activity search.")
        try:
            token = self.amadeus_auth.get_access_token()

            if token is None:
                raise ValueError("Amadeus auth token is missing")

            coords: tuple[float, float] | None = self._get_coordinates(token, location)
            if not coords:
                raise ValueError(f"Could not find coordinates for location: {location}")

            lat, lon = coords

            url = f"{self.amadeus_auth.base_url}/v1/shopping/activities"
            headers = {"Authorization": f"Bearer {token}"}
            params = {"latitude": lat, "longitude": lon, "radius": radius}

            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            if not data.get("data"):
                raise ValueError(f"No activities found for location: {location}")

            results: List[ActivityResultState] = []
            for item in data["data"][:max_places]:

                # Price formatting
                price_data = item.get("price", {})
                amount = price_data.get("amount", "N/A")
                currency = price_data.get("currencyCode", "")
                price_str = (
                    f"{amount} {currency}" if amount != "N/A" else "Price not available"
                )

                results.append(
                    ActivityResultState(
                        name=item.get("name", "Unnamed Activity"),
                        price=price_str,
                        booking_link=item.get("bookingLink", "No link available"),
                        short_description=item.get(
                            "shortDescription", "No description"
                        ),
                    )
                )

            return results

        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {str(e)}")
            return []
        except Exception as e:
            print(f"Error: {str(e)}")
            return []

    async def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async not supported yet")
