from typing import Optional
from pydantic import BaseModel, Field


class PlanDetailsState(BaseModel):
    """The structured output from the 'Brain'"""

    destination: Optional[str] = Field(description="Destination city and country")
    origin: Optional[str] = Field(description="Origin city and country")
    departure_date: Optional[str] = Field(description="Departure date")
    arrival_date: Optional[str] = Field(description="Arrival date")
    budget: Optional[float] = Field(description="Total budget for the trip")
    remaining_budget: Optional[float] = Field(
        description="Remaining budget for the trip"
    )
    interests: Optional[str] = Field(
        description="User interests for activity suggestions"
    )
    need_hotel: Optional[bool] = Field(
        description="Whether the user needs hotel suggestions"
    )
    need_activities: Optional[bool] = Field(
        description="Whether the user needs activity suggestions"
    )
