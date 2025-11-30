from pydantic import BaseModel, Field


class PlanDetailsState(BaseModel):
    """The structured output from the 'Brain'"""

    destination: str = Field(description="Destination city and country")
    origin: str = Field(description="Origin city and country")
    departure_date: str = Field(description="Departure date")
    arrival_date: str = Field(description="Arrival date")
    total_budget: float = Field(description="Total budget for the trip")
    remaining_budget: float = Field(description="Remaining budget for the trip")
    interests: str = Field(description="User interests for activity suggestions")
    need_hotel: bool = Field(description="Whether the user needs hotel suggestions")
    need_activities: bool = Field(
        description="Whether the user needs activity suggestions"
    )
