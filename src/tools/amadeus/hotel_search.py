from typing import List, Optional
from pydantic import BaseModel, Field
import requests
from typing import Type
from langchain.tools import BaseTool

from .auth import AmadeusAuth


class HotelContact(BaseModel):
    phone: Optional[str]
    fax: Optional[str]


class HotelLocation(BaseModel):
    city_code: str
    latitude: Optional[float]
    longitude: Optional[float]


class PriceDetails(BaseModel):
    total: str
    currency: str
    avg_nightly: Optional[str]
    taxes: Optional[str]


class RoomDetails(BaseModel):
    room_type: str
    beds: Optional[int]
    bed_type: Optional[str]
    description: str


class OfferDetails(BaseModel):
    offer_id: str
    check_in: str
    check_out: str
    board_type: str
    guests: int
    price: PriceDetails
    room: RoomDetails
    cancellation_policy: Optional[str]
    booking_link: Optional[str]


class HotelDetails(BaseModel):
    hotel_id: str
    name: str
    contact: Optional[HotelContact]
    location: HotelLocation
    offers: List[OfferDetails]


class HotelSearchResult(BaseModel):
    city_code: str
    hotels: List[HotelDetails]


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
    ) -> HotelSearchResult:
        """Search for hotels"""
        try:
            token = self.amadeus_auth.get_access_token()

            # Step 1: Get hotel IDs in the city
            hotel_ids = self._get_hotel_ids_by_city(
                token,
                city_code,
                radius,
                max_hotels=20,
            )

            if not hotel_ids:
                return HotelSearchResult(city_code=city_code, hotels=[])

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
                return HotelSearchResult(city_code=city_code, hotels=[])

            hotels = []

            for hotel_data in data["data"][:max_results]:
                hotel = hotel_data.get("hotel", {})
                offers = hotel_data.get("offers", [])

                if not offers:
                    continue

                hotel_details = HotelDetails(
                    hotel_id=hotel.get("hotelId", "N/A"),
                    name=hotel.get("name", "Unknown Hotel"),
                    contact=HotelContact(
                        phone=hotel.get("contact", {}).get("phone"),
                        fax=hotel.get("contact", {}).get("fax"),
                    ),
                    location=HotelLocation(
                        city_code=hotel.get("cityCode", "N/A"),
                        latitude=hotel.get("latitude"),
                        longitude=hotel.get("longitude"),
                    ),
                    offers=[
                        OfferDetails(
                            offer_id=offer.get("id", "N/A"),
                            check_in=offer.get("checkInDate", "N/A"),
                            check_out=offer.get("checkOutDate", "N/A"),
                            board_type=offer.get("boardType", "N/A"),
                            guests=offer.get("guests", {}).get("adults", "N/A"),
                            price=PriceDetails(
                                total=offer.get("price", {}).get("total", "N/A"),
                                currency=offer.get("price", {}).get("currency", ""),
                                avg_nightly=offer.get("price", {})
                                .get("variations", {})
                                .get("average", {})
                                .get("total"),
                                taxes=(
                                    "; ".join(
                                        [
                                            f"{t.get('amount', 'N/A')} {t.get('currency', '')} ({t.get('code', '')})"
                                            for t in offer.get("price", {}).get(
                                                "taxes", []
                                            )
                                        ]
                                    )
                                    if offer.get("price", {}).get("taxes")
                                    else None
                                ),
                            ),
                            room=RoomDetails(
                                room_type=offer.get("room", {})
                                .get("typeEstimated", {})
                                .get("category", "Standard"),
                                beds=offer.get("room", {})
                                .get("typeEstimated", {})
                                .get("beds"),
                                bed_type=offer.get("room", {})
                                .get("typeEstimated", {})
                                .get("bedType"),
                                description=offer.get("room", {})
                                .get("description", {})
                                .get("text", "No description available"),
                            ),
                            cancellation_policy=offer.get("policies", {})
                            .get("refundable", {})
                            .get("cancellationRefund"),
                            booking_link=offer.get("self"),
                        )
                        for offer in offers
                    ],
                )

                hotels.append(hotel_details)

            return HotelSearchResult(city_code=city_code, hotels=hotels)

        except requests.exceptions.HTTPError as e:
            raise Exception(f"API Error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise Exception(f"Error searching hotels: {str(e)}")

    async def _arun(self, *args, **kwargs):
        """Async version - not implemented"""
        raise NotImplementedError("Async not supported yet")
