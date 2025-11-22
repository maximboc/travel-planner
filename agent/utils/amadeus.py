"""
Amadeus API Tools for LangChain Travel Planning Agent
Includes Flight Search and Hotel Accommodation Search
"""

import os
import requests
from typing import Optional, Type, List
from datetime import datetime
from pydantic import BaseModel, Field
from langchain.tools import BaseTool


class AmadeusAuth:
    """Handle Amadeus API authentication"""

    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://test.api.amadeus.com"  # Use production URL in prod
        self.access_token = None
        self.token_expires_at = None

    def get_access_token(self) -> str:
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
    """Tool for searching flight offers using Amadeus Flight Offers Search API"""

    name: str = "search_flights"
    description: str = """
    Search for available flight offers between two cities.
    Use this tool when users want to find flights, compare prices, or plan air travel.
    Returns flight details including prices, airlines, duration, and layover information.
    Input should include origin, destination, and departure date at minimum.
    """
    amadeus_auth: AmadeusAuth = None

    def __init__(self, amadeus_auth: AmadeusAuth):
        super().__init__()
        self.amadeus_auth = amadeus_auth

    args_schema: Type[BaseModel] = FlightSearchInput

    def _run(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        adults: int = 1,
        travel_class: str = "ECONOMY",
        max_results: int = 5,
    ) -> str:
        """Search for flights"""
        try:
            token = self.amadeus_auth.get_access_token()
            url = f"{self.amadeus_auth.base_url}/v2/shopping/flight-offers"

            headers = {"Authorization": f"Bearer {token}"}
            params = {
                "originLocationCode": origin.upper(),
                "destinationLocationCode": destination.upper(),
                "departureDate": departure_date,
                "adults": adults,
                "travelClass": travel_class.upper(),
                "max": max_results,
            }

            if return_date:
                params["returnDate"] = return_date

            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()

            data = response.json()

            if not data.get("data"):
                return "No flight offers found for the specified criteria."

            # Format results
            results = []
            for idx, offer in enumerate(data["data"][:max_results], 1):
                price = offer["price"]["total"]
                currency = offer["price"]["currency"]

                itineraries_info = []
                for itin in offer["itineraries"]:
                    segments = itin["segments"]
                    departure = segments[0]["departure"]
                    arrival = segments[-1]["arrival"]
                    duration = itin["duration"]

                    airline = segments[0]["carrierCode"]
                    stops = len(segments) - 1

                    itin_str = (
                        f"  {departure['iataCode']} → {arrival['iataCode']} | "
                        f"Departs: {departure['at']} | Arrives: {arrival['at']} | "
                        f"Duration: {duration} | Stops: {stops} | Airline: {airline}"
                    )
                    itineraries_info.append(itin_str)

                result = f"\nFlight Offer {idx}:\n"
                result += f"Price: {price} {currency}\n"
                result += "\n".join(itineraries_info)
                results.append(result)

            summary = f"Found {len(results)} flight offer(s) from {origin} to {destination}:\n"
            return summary + "\n".join(results)

        except requests.exceptions.HTTPError as e:
            return f"API Error: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return f"Error searching flights: {str(e)}"

    async def _arun(self, *args, **kwargs):
        """Async version - not implemented"""
        raise NotImplementedError("Async not supported yet")


class HotelSearchInput(BaseModel):
    """Input schema for hotel search"""

    city_code: str = Field(
        description="City IATA code (e.g., 'PAR' for Paris, 'NYC' for New York)"
    )
    check_in_date: str = Field(description="Check-in date in YYYY-MM-DD format")
    check_out_date: str = Field(description="Check-out date in YYYY-MM-DD format")
    adults: int = Field(1, description="Number of adult guests (default: 1)")
    room_quantity: int = Field(1, description="Number of rooms (default: 1)")
    radius: Optional[int] = Field(
        5, description="Search radius in kilometers (default: 5)"
    )
    max_results: int = Field(
        5, description="Maximum number of hotels to return (default: 5)"
    )


class HotelSearchTool(BaseTool):
    """Tool for searching hotel accommodations using Amadeus Hotel List + Hotel Search APIs"""

    name: str = "search_hotels"
    description: str = """
    Search for available hotel accommodations in a city.
    Use this tool when users want to find hotels, compare prices, or plan accommodation.
    Returns hotel details including prices, names, addresses, and room descriptions.
    Input requires city code, check-in date, and check-out date at minimum.
    """
    args_schema: Type[BaseModel] = HotelSearchInput
    amadeus_auth: AmadeusAuth = None

    def __init__(self, amadeus_auth: AmadeusAuth):
        super().__init__()
        self.amadeus_auth = amadeus_auth

    def _get_hotel_ids_by_city(
        self, token: str, city_code: str, radius: int = 5, max_hotels: int = 20
    ) -> List[str]:
        """Step 1: Get hotel IDs from Hotel List API"""
        url = f"{self.amadeus_auth.base_url}/v1/reference-data/locations/hotels/by-city"

        headers = {"Authorization": f"Bearer {token}"}
        params = {
            "cityCode": city_code.upper(),
            "radius": radius,
            "radiusUnit": "KM",
            "hotelSource": "ALL",
        }

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        data = response.json()

        if not data.get("data"):
            return []

        # Extract hotel IDs (limit to max_hotels)
        hotel_ids = [hotel["hotelId"] for hotel in data["data"][:max_hotels]]
        return hotel_ids

    def _run(
        self,
        city_code: str,
        check_in_date: str,
        check_out_date: str,
        adults: int = 1,
        room_quantity: int = 1,
        radius: int = 5,
        max_results: int = 5,
    ) -> str:
        """Search for hotels"""
        try:
            token = self.amadeus_auth.get_access_token()

            # Step 1: Get hotel IDs in the city
            hotel_ids = self._get_hotel_ids_by_city(
                token,
                city_code,
                radius,
                max_hotels=20,  # Get more IDs to increase chances of finding offers
            )

            if not hotel_ids:
                return f"No hotels found in {city_code}."

            # Step 2: Search for offers using hotel IDs
            url = f"{self.amadeus_auth.base_url}/v3/shopping/hotel-offers"

            headers = {"Authorization": f"Bearer {token}"}
            params = {
                "hotelIds": ",".join(hotel_ids),
                "checkInDate": check_in_date,
                "checkOutDate": check_out_date,
                "adults": adults,
                "roomQuantity": room_quantity,
                "paymentPolicy": "NONE",
                "bestRateOnly": "true",
            }

            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()

            data = response.json()

            if not data.get("data"):
                return (
                    f"No hotel offers available in {city_code} for the specified dates."
                )

            # Format results
            results = []

            for idx, hotel_data in enumerate(data["data"][:max_results], 1):
                hotel = hotel_data.get("hotel", {})
                offers = hotel_data.get("offers", [])

                if not offers:
                    continue

                offer = offers[0]  # Get best/suggested rate

                # Basic hotel info
                hotel_name = hotel.get("name", "Unknown Hotel")
                hotel_id = hotel.get("hotelId", "N/A")
                city_code_resp = hotel.get("cityCode", "N/A")
                latitude = hotel.get("latitude", "N/A")
                longitude = hotel.get("longitude", "N/A")

                # Contact info
                contact = hotel.get("contact", {}) or {}
                phone = contact.get("phone")
                fax = contact.get("fax")

                # Offer / stay info
                offer_id = offer.get("id", "N/A")
                check_in = offer.get("checkInDate", "N/A")
                check_out = offer.get("checkOutDate", "N/A")
                board_type = offer.get("boardType", "N/A")
                guests_info = offer.get("guests", {})
                adults = guests_info.get("adults", "N/A")

                # Price info (be defensive)
                price_info = offer.get("price", {})
                total_price = price_info.get("total") or price_info.get("base") or "N/A"
                currency = price_info.get("currency", "")

                # Taxes breakdown
                taxes = price_info.get("taxes", []) or []
                taxes_str = ""
                if taxes:
                    taxes_lines = []
                    for t in taxes:
                        t_amt = t.get("amount", "N/A")
                        t_curr = t.get("currency", currency or "")
                        t_code = t.get("code")
                        included = t.get("included")
                        line = f"{t_amt} {t_curr}"
                        if t_code:
                            line += f" ({t_code})"
                        if included is True:
                            line += " [included]"
                        taxes_lines.append(line)
                    taxes_str = "; ".join(taxes_lines)

                # Variations / nightly average
                variations = price_info.get("variations", {}) or {}
                avg_nightly = None
                if "average" in variations and isinstance(variations["average"], dict):
                    avg_nightly = variations["average"].get("total") or variations[
                        "average"
                    ].get("base")

                # Room info and description
                room = offer.get("room", {})
                room_type = room.get("typeEstimated", {}).get("category") or room.get(
                    "type", "Standard"
                )
                bed_info = room.get("typeEstimated", {}) or {}
                beds = bed_info.get("beds", "N/A")
                bed_type = bed_info.get("bedType", "N/A")
                room_desc = (
                    room.get("description", {}).get("text")
                    or offer.get("roomInformation", {}).get("description")
                    or "No description available"
                )

                # Policies
                policies = offer.get("policies", {})
                refundable_info = policies.get("refundable", {}) if policies else {}
                cancellation = (
                    refundable_info.get("cancellationRefund")
                    if refundable_info
                    else None
                )

                # Booking/link
                self_link = offer.get("self") or hotel_data.get("self") or ""

                # Build formatted result
                result_lines = [f"\nHotel {idx}: {hotel_name}"]
                result_lines.append(f"Hotel ID: {hotel_id}")
                result_lines.append(f"Offer ID: {offer_id}")
                result_lines.append(
                    f"Location: {city_code_resp} (Lat: {latitude}, Lon: {longitude})"
                )
                if phone:
                    result_lines.append(f"Contact Phone: {phone}")
                if fax:
                    result_lines.append(f"Contact Fax: {fax}")
                result_lines.append(
                    f"Stay: {check_in} → {check_out} | Guests (adults): {adults} | Board: {board_type}"
                )

                # Price block
                price_line = f"Price: {total_price} {currency}".strip()
                if avg_nightly:
                    price_line += f" | Avg/night: {avg_nightly} {currency}"
                result_lines.append(price_line)
                if taxes_str:
                    result_lines.append(f"Taxes: {taxes_str}")

                # Room block
                result_lines.append(f"Room Type: {room_type} | Beds: {beds} {bed_type}")
                # Keep description reasonable length
                desc_clean = room_desc.replace("\n", " ").strip()
                max_desc = 300
                if len(desc_clean) > max_desc:
                    desc_clean = desc_clean[: max_desc - 3] + "..."
                result_lines.append(f"Description: {desc_clean}")

                # Policies
                if cancellation:
                    result_lines.append(f"Refundable/Cancellation: {cancellation}")

                # Offer link
                if self_link:
                    result_lines.append(f"Booking Link: {self_link}")

                results.append("\n".join(result_lines))

            if not results:
                return f"Hotels found in {city_code}, but no offers available for the specified dates."

            summary = f"Found {len(results)} hotel offer(s) in {city_code}:\n"
            return summary + "\n".join(results)

        except requests.exceptions.HTTPError as e:
            return f"API Error: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return f"Error searching hotels: {str(e)}"

    async def _arun(self, *args, **kwargs):
        """Async version - not implemented"""
        raise NotImplementedError("Async not supported yet")


"""
# Example usage
if __name__ == "__main__":
    # Initialize auth (set your credentials via environment variables)
    amadeus_auth = AmadeusAuth(
        api_key="VQGubWZXZoGBV8eyUpPMPtNM9IG5AF20",  # os.getenv("AMADEUS_API_KEY", ""),
        api_secret="W1p33Wp7AzR4SZrN",  # os.getenv("AMADEUS_API_SECRET", "YOUR_API_SECRET")
    )
    # Initialize the tools
    flight_tool = FlightSearchTool()
    hotel_tool = HotelSearchTool()

    # Example flight search
    print("=== FLIGHT SEARCH ===")
    flight_result = flight_tool._run(
        origin="JFK",
        destination="CDG",
        departure_date="2025-12-15",
        return_date="2025-12-22",
        adults=2,
        travel_class="ECONOMY",
    )
    print(flight_result)

    print("\n" + "=" * 80)
    print("=== HOTEL SEARCH ===")
    hotel_result = hotel_tool._run(
        city_code="PAR",
        check_in_date="2025-12-15",
        check_out_date="2025-12-22",
        adults=2,
        room_quantity=1,
    )
    print(hotel_result)

    # To use with LangChain agent:
    # from langchain.agents import initialize_agent, AgentType
    # from langchain_openai import ChatOpenAI
    #
    # tools = [flight_tool, hotel_tool]
    # llm = ChatOpenAI(model="gpt-4", temperature=0)
    # agent = initialize_agent(
    #     tools,
    #     llm,
    #     agent=AgentType.OPENAI_FUNCTIONS,
    #     verbose=True
    # )
    #
    # agent.run("Find me flights from New York to Paris for December 15-22 and hotels in Paris")
"""
