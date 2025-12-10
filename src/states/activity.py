from pydantic import BaseModel, Field


class ActivityResultState(BaseModel):
    """Output schema for activity search"""

    name: str = Field(description="Name of the activity")
    amount: float = Field(description="Price of the activity")
    currency: str = Field(description="Currency of the activity price (e.g., 'USD', 'EUR')")
    booking_link: str = Field(description="Link to book the activity")
    short_description: str = Field(description="Short description of the activity")
