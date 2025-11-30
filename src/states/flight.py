from typing import List
from pydantic import BaseModel, Field


class FlightSegment(BaseModel):
    """Represents a single flight segment in an itinerary"""

    departure_airport: str = Field(description="IATA code of the departure airport")
    arrival_airport: str = Field(description="IATA code of the arrival airport")
    departure_time: str = Field(description="Departure time in ISO 8601 format")
    arrival_time: str = Field(description="Arrival time in ISO 8601 format")
    duration: str = Field(description="Duration of the flight")
    airline: str = Field(description="IATA code of the airline")
    stops: int = Field(description="Number of stops in the flight")


class FlightItinerary(BaseModel):
    """Represents an itinerary with multiple flight segments"""

    segments: List[FlightSegment] = Field(
        description="List of flight segments in the itinerary"
    )


class FlightSearchResultState(BaseModel):
    """Represents a single flight offer result"""

    price: str = Field(description="Total price of the flight offer")
    currency: str = Field(description="Currency of the flight offer")
    itineraries: List[FlightItinerary] = Field(description="List of flight itineraries")
