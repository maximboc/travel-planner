import requests
from typing import Any, Dict, Optional, List, Type
from pydantic import BaseModel, Field
from langchain.tools import BaseTool

from .auth import AmadeusAuth
from src.states import FlightSearchResultState, FlightItinerary, FlightSegment


class FlightSearchInput(BaseModel):
    """Input schema for flight search"""

    origin: str = Field(description="Origin airport IATA code (e.g., 'JFK', 'LAX')")
    destination: str = Field(
        description="Destination airport IATA code (e.g., 'LHR', 'CDG')"
    )
    departure_date: str = Field(description="Departure date in YYYY-MM-DD format")
    return_date: Optional[str] = Field(
        None, description="Return date for round-trip in YYYY-MM-DD format"
    )
    adults: int = Field(1, description="Number of adult passengers (default: 1)")
    travel_class: Optional[str] = Field(
        "ECONOMY",
        description="Travel class: ECONOMY, PREMIUM_ECONOMY, BUSINESS, or FIRST",
    )
    max_results: int = Field(
        5, description="Maximum number of flight offers to return (default: 5)"
    )


class FlightSearchTool(BaseTool):
    """Tool for searching flights using Amadeus Flight Search APIs"""

    name: str = "search_flights"
    description: str = """
    Search for available flights between two cities.
    Use this tool when users want to find flights, compare prices, or plan air travel.
    Returns flight details including prices, airlines, duration, and layover information.
    Input requires origin, destination, departure date, and optionally return date.
    """
    args_schema: Type[BaseModel] = FlightSearchInput
    amadeus_auth: AmadeusAuth | None = None

    def __init__(self, amadeus_auth: AmadeusAuth | None = None):
        super().__init__()
        self.amadeus_auth = amadeus_auth

    def _run(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        adults: int = 1,
        travel_class: str = "ECONOMY",
        max_results: int = 5,
    ) -> List[FlightSearchResultState]:
        """Search for flights"""
        try:
            if not self.amadeus_auth:
                raise ValueError("AmadeusAuth instance is required for flight search.")

            token = self.amadeus_auth.get_access_token()
            url = f"{self.amadeus_auth.base_url}/v2/shopping/flight-offers"

            headers: Dict[str, str] = {"Authorization": f"Bearer {token}"}
            params: Dict[str, Any] = {
                "originLocationCode": origin.upper(),
                "destinationLocationCode": destination.upper(),
                "departureDate": departure_date,
                "adults": adults,
                "travelClass": travel_class,
                "max": max_results,
            }

            if return_date:
                params["returnDate"] = return_date

            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()

            data = response.json()

            if not data.get("data"):
                return []

            # Parse results
            results: List[FlightSearchResultState] = []
            for offer in data["data"][:max_results]:
                price = offer["price"]["total"]
                currency = offer["price"]["currency"]

                itineraries: List[FlightItinerary] = []
                for itin in offer["itineraries"]:
                    segments: List[FlightSegment] = []
                    for segment in itin["segments"]:
                        segments.append(
                            FlightSegment(
                                departure_airport=segment["departure"]["iataCode"],
                                arrival_airport=segment["arrival"]["iataCode"],
                                departure_time=segment["departure"]["at"],
                                arrival_time=segment["arrival"]["at"],
                                duration=segment["duration"],
                                airline=segment["carrierCode"],
                                stops=len(itin["segments"]) - 1,
                            )
                        )
                    itineraries.append(FlightItinerary(segments=segments))

                results.append(
                    FlightSearchResultState(
                        price=price,
                        currency=currency,
                        itineraries=itineraries,
                    )
                )

            return results

        except requests.exceptions.HTTPError as e:
            raise ValueError(f"API Error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise ValueError(f"Error searching flights: {str(e)}")
