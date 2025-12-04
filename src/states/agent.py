from pydantic import BaseModel, Field
from typing import Optional, List, Annotated
from .planner import PlanDetailsState
from .flight import FlightSearchResultState
from .hotel import HotelSearchState
from .activity import ActivityResultState
from langgraph.graph.message import add_messages

from enum import Enum


class TravelClass(str, Enum):
    ECONOMY = "ECONOMY"
    BUSINESS = "BUSINESS"
    FIRST = "FIRST"


def replace_value(old_val, new_val):
    return new_val


class AgentState(BaseModel):
    # Core Messages & Plan
    messages: Annotated[list, add_messages] = Field(default_factory=list)
    plan: Annotated[Optional[PlanDetailsState], replace_value] = Field(
        default=None, description="Details of the travel plan"
    )

    # User Input Handling
    needs_user_input: Annotated[bool, replace_value] = Field(
        default=False, description="Indicates if more user input is needed"
    )
    validation_question: Annotated[Optional[str], replace_value] = Field(
        default=None, description="Question to ask the user for clarification"
    )
    last_node: Annotated[Optional[str], replace_value] = Field(
        default=None, description="The last executed node in the agent workflow"
    )

    # Passenger Info
    adults: Annotated[Optional[int], replace_value] = Field(
        default=None, description="Number of adult travelers"
    )
    children: Annotated[Optional[int], replace_value] = Field(
        default=None, description="Number of child travelers (ages 2-11)"
    )
    infants: Annotated[Optional[int], replace_value] = Field(
        default=None, description="Number of infant travelers (under 2 years)"
    )
    travel_class: Annotated[Optional[TravelClass], replace_value] = Field(
        default=None, description="Travel class (ECONOMY, BUSINESS, FIRST)"
    )

    # Depart / Arrival
    city_code: Annotated[Optional[str], replace_value] = Field(
        default=None, description="IATA code of the destination city"
    )
    origin_code: Annotated[Optional[str], replace_value] = Field(
        default=None, description="IATA code of the origin city"
    )

    # Flights
    flight_data: Annotated[Optional[List[FlightSearchResultState]], replace_value] = (
        Field(default=None, description="Flight search results")
    )
    selected_flight_index: Annotated[Optional[int], replace_value] = Field(
        default=None, description="Index of the selected flight"
    )

    # Hotels
    hotel_data: Annotated[Optional[HotelSearchState], replace_value] = Field(
        default=None, description="Hotel search results"
    )
    selected_hotel_index: Annotated[Optional[int], replace_value] = Field(
        default=None, description="Index of the selected hotel"
    )

    # Activities
    activity_data: Annotated[Optional[List[ActivityResultState]], replace_value] = (
        Field(default=None, description="Activity search results")
    )
    final_itinerary: Annotated[Optional[str], replace_value] = Field(
        default=None, description="Final itinerary details"
    )

    # Review & Feedback
    feedback: Annotated[Optional[str], replace_value] = Field(
        default=None, description="User feedback"
    )
    revision_count: Annotated[int, replace_value] = Field(
        default=0, description="Number of times the plan has been revised"
    )
    with_reasoning: Annotated[bool, replace_value] = Field(
        default=True, description="Enable or disable the review step"
    )
    with_planner: Annotated[bool, replace_value] = Field(
        default=True, description="Enable or disable the planner"
    )
    with_tools: Annotated[bool, replace_value] = Field(
        default=True, description="Enable or disable the tools"
    )
