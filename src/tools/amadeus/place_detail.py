from typing import TypedDict, List
import requests
from langsmith import traceable
from langchain.tools import tool


class PlaceDetailResult(TypedDict):
    """Custom exception for place detail tool errors."""

    name: str
    address: str
    latitude: float
    longitude: float


@tool
@traceable(run_type="tool", name="get_place_details")
def get_place_details(query: str) -> PlaceDetailResult:
    """
    Searches for locations/activities using OpenStreetMap.

    IMPORTANT: This tool works only with the following specific categories : (Parks, Museums, Cinemas or Restaurants) + the city's name.

    Args:
        query: The search string. Combine the category and the city (e.g., 'Parks in London').

    Returns:
        A formatted string of the top 3 matching locations with coordinates.
    """
    try:
        headers = {"User-Agent": "LangChainTravelAgent/1.0"}
        url = "https://nominatim.openstreetmap.org/search"

        params = {
            "q": query.strip(),
            "format": "jsonv2",
            "addressdetails": 1,
            "limit": 3,
        }

        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data:
            return f"No results found for '{query}'. Try a broader category (e.g., 'Museums' instead of 'Modern Art')."

        results: List[PlaceDetailResult] = []
        for i, item in enumerate(data, 1):
            name = item.get("display_name", "N/A")
            address = item.get("address", {})
            formatted_address = ", ".join(address.values())
            latitude = float(item.get("lat", 0.0))
            longitude = float(item.get("lon", 0.0))

            results.append(
                PlaceDetailResult(
                    name=name,
                    address=formatted_address,
                    latitude=latitude,
                    longitude=longitude,
                )
            )
        return results

    except Exception as e:
        return f"Error searching map: {str(e)}"
