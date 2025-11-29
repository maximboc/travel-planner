import requests
from typing import Optional, Type, List
from pydantic import BaseModel, Field
from .auth import AmadeusAuth
from langchain.tools import tool


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


class FlightSegment(BaseModel):
    """Represents a single flight segment in an itinerary"""

    departure_airport: str
    arrival_airport: str
    departure_time: str
    arrival_time: str
    duration: str
    airline: str
    stops: int


class FlightItinerary(BaseModel):
    """Represents an itinerary with multiple flight segments"""

    segments: List[FlightSegment]


class FlightSearchResult(BaseModel):
    """Represents a single flight offer result"""

    price: str
    currency: str
    itineraries: List[FlightItinerary]


def create_flight_search_tool(amadeus_auth: AmadeusAuth):
    @tool
    def flight_search_tool(
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        adults: int = 1,
        travel_class: str = "ECONOMY",
        max_results: int = 5,
    ) -> List[dict]:
        """
        Search for available flight offers between two cities.
        Use this tool when users want to find flights, compare prices, or plan air travel.
        Returns flight details including prices, airlines, duration, and layover information.

        Args:
            origin: Origin airport IATA code (e.g., 'JFK', 'LAX')
            destination: Destination airport IATA code (e.g., 'LHR', 'CDG')
            departure_date: Departure date in YYYY-MM-DD format
            return_date: Return date for round-trip in YYYY-MM-DD format (optional)
            adults: Number of adult passengers (default: 1)
            travel_class: Travel class: ECONOMY, PREMIUM_ECONOMY, BUSINESS, or FIRST
            max_results: Maximum number of flight offers to return (default: 5)
        """
        try:
            token = amadeus_auth.get_access_token()
            url = f"{amadeus_auth.base_url}/v2/shopping/flight-offers"

            headers = {"Authorization": f"Bearer {token}"}
            params = {
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
            results = []
            for offer in data["data"][:max_results]:
                price = offer["price"]["total"]
                currency = offer["price"]["currency"]

                itineraries = []
                for itin in offer["itineraries"]:
                    segments = []
                    for segment in itin["segments"]:
                        segments.append(
                            {
                                "departure_airport": segment["departure"]["iataCode"],
                                "arrival_airport": segment["arrival"]["iataCode"],
                                "departure_time": segment["departure"]["at"],
                                "arrival_time": segment["arrival"]["at"],
                                "duration": segment["duration"],
                                "airline": segment["carrierCode"],
                                "stops": len(itin["segments"]) - 1,
                            }
                        )
                    itineraries.append({"segments": segments})

                results.append(
                    {
                        "price": price,
                        "currency": currency,
                        "itineraries": itineraries,
                    }
                )

            return results

        except requests.exceptions.HTTPError as e:
            raise ValueError(f"API Error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise ValueError(f"Error searching flights: {str(e)}")

    return flight_search_tool
