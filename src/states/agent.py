from pydantic import BaseModel, Field
from typing import Optional, List

from .planner import PlanDetailsState
from .flight import FlightSearchResultState
from .hotel import HotelSearchState
from .activity import ActivityResultState


class AgentState(BaseModel):
    messages: List = Field(default_factory=list)
    plan: Optional[PlanDetailsState] = Field(
        default=None, description="Details of the travel plan"
    )
    city_code: Optional[str] = Field(
        default=None, description="IATA code of the destination city"
    )
    origin_code: Optional[str] = Field(
        default=None, description="IATA code of the origin city"
    )
    flight_data: Optional[List[FlightSearchResultState]] = Field(
        default=None, description="Flight search results"
    )
    hotel_data: Optional[HotelSearchState] = Field(
        default=None, description="Hotel search results"
    )
    activity_data: Optional[List[ActivityResultState]] = Field(
        default=None, description="Activity search results"
    )
    final_itinerary: Optional[str] = Field(
        default=None, description="Final itinerary details"
    )
    feedback: Optional[str] = Field(default=None, description="User feedback")
    revision_count: int = Field(
        default=0, description="Number of times the plan has been revised"
    )
