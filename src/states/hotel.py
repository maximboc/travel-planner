from typing import List, Optional
from pydantic import BaseModel, Field


class HotelContact(BaseModel):
    phone: Optional[str] = Field(None, description="Hotel phone number")
    fax: Optional[str] = Field(None, description="Hotel fax number")


class HotelLocation(BaseModel):
    city_code: str = Field(description="City code where the hotel is located")
    latitude: Optional[float] = Field(None, description="Latitude of the hotel")
    longitude: Optional[float] = Field(None, description="Longitude of the hotel")


class PriceDetails(BaseModel):
    total: str = Field(description="Total price for the hotel stay")
    currency: str = Field(description="Currency code for the price")
    avg_nightly: Optional[str] = Field(None, description="Average nightly price")
    taxes: Optional[str] = Field(None, description="Taxes and fees")


class RoomDetails(BaseModel):
    room_type: str = Field(description="Type of the room")
    beds: Optional[int] = Field(None, description="Number of beds in the room")
    bed_type: Optional[str] = Field(None, description="Type of beds in the room")
    description: str = Field(description="Description of the room")


class OfferDetails(BaseModel):
    offer_id: str = Field(description="Unique identifier for the offer")
    check_in: str = Field(description="Check-in date")
    check_out: str = Field(description="Check-out date")
    board_type: str = Field(description="Board type (e.g., 'BB', 'HB')")
    guests: int = Field(description="Number of guests")
    price: PriceDetails = Field(description="Price details for the offer")
    room: RoomDetails = Field(description="Room details for the offer")
    cancellation_policy: Optional[str] = Field(
        None, description="Cancellation policy for the offer"
    )
    booking_link: Optional[str] = Field(None, description="Booking link for the offer")


class HotelDetails(BaseModel):
    hotel_id: str = Field(description="Unique identifier for the hotel")
    name: str = Field(description="Name of the hotel")
    contact: Optional[HotelContact] = Field(
        None, description="Contact details for the hotel"
    )
    location: HotelLocation = Field(description="Location details for the hotel")
    offers: List[OfferDetails] = Field(
        description="List of offers available for the hotel"
    )


class HotelSearchState(BaseModel):
    city_code: str = Field(description="City code for the hotel search")
    hotels: List[HotelDetails] = Field(description="List of hotels found in the search")
