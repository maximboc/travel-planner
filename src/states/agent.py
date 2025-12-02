from pydantic import BaseModel, Field
from typing import Optional, List

from .planner import PlanDetailsState
from .flight import FlightSearchResultState
from .hotel import HotelSearchState
from .activity import ActivityResultState

from enum import Enum

class TravelClass(str, Enum):
    ECONOMY = "ECONOMY"
    BUSINESS = "BUSINESS"
    FIRST = "FIRST"


class AgentState(BaseModel):
    # Core Messages & Plan
    messages: List = Field(default_factory=list)
    plan: Optional[PlanDetailsState] = Field(
        default=None, description="Details of the travel plan"
    )

    # User Input Handling
    needs_user_input: bool = Field(
        default=False, description="Indicates if more user input is needed"
    )
    validation_question: Optional[str] = Field(
        default=None, description="Question to ask the user for clarification"
    )

    # Passenger Info
    adults: Optional[int] = Field(default=None, description="Number of adult travelers")
    children: Optional[int] = Field(
        default=None, description="Number of child travelers (ages 2-11)"
    )
    infants: Optional[int] = Field(
        default=None, description="Number of infant travelers (under 2 years)"
    )
    travel_class: Optional[TravelClass] = Field(
        default=None,
        description="Travel class (ECONOMY, BUSINESS, FIRST)"
    )

    # Depart / Arrival
    city_code: Optional[str] = Field(
        default=None, description="IATA code of the destination city"
    )
    origin_code: Optional[str] = Field(
        default=None, description="IATA code of the origin city"
    )
    # Flights
    flight_data: Optional[List[FlightSearchResultState]] = Field(
        default=None, description="Flight search results"
    )
    selected_flight_index: Optional[int] = Field(
        default=None, description="Index of the selected flight"
    )

    # Hotels
    hotel_data: Optional[HotelSearchState] = Field(
        default=None, description="Hotel search results"
    )
    selected_hotel_index: Optional[int] = Field(
        default=None, description="Index of the selected hotel"
    )

    # Activities
    activity_data: Optional[List[ActivityResultState]] = Field(
        default=None, description="Activity search results"
    )
    final_itinerary: Optional[str] = Field(
        default=None, description="Final itinerary details"
    )

    # Review & Feedback
    feedback: Optional[str] = Field(default=None, description="User feedback")
    revision_count: int = Field(
        default=0, description="Number of times the plan has been revised"
    )
