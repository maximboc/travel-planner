from pydantic import BaseModel, Field
import requests
from typing import Dict, Type, Optional
from .auth import AmadeusAuth
from langchain.tools import BaseTool
import time


class CitySearchInput(BaseModel):
    """Input schema for city/airport search"""

    keyword: str = Field(description="The name of the city or airport")
    subType: str = Field(
        "CITY", description="The type of location: CITY or AIRPORT. Default: CITY"
    )


class CitySearchResult(BaseModel):
    """Output schema for city/airport search result"""

    name: str = Field(description="Name of the city or airport")
    iata_code: str = Field(description="IATA code of the city or airport")


class CitySearchTool(BaseTool):
    last_called: Optional[str] = None
    """Tool for searching for IATA/City codes using Amadeus Location API"""
    name: str = "get_city_code"
    description: str = "Searches for Amadeus City Code. Returns None if not found."
    args_schema: Type[BaseModel] = CitySearchInput
    amadeus_auth: AmadeusAuth | None = None

    def __init__(self, amadeus_auth: AmadeusAuth | None = None):
        super().__init__()
        self.amadeus_auth = amadeus_auth

    def _run(self, keyword: str, subType: str = "CITY") -> Optional[CitySearchResult]:
        """Search for city/location code"""
        if not self.amadeus_auth:
            raise ValueError("AmadeusAuth instance is required for city search.")
        if self.last_called is not None:
            sleep_time = 1 - (
                time.time()
                - time.mktime(time.strptime(self.last_called, "%Y-%m-%d %H:%M:%S"))
            )
            if sleep_time > 0:
                time.sleep(sleep_time)
        self.last_called = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        try:
            token = self.amadeus_auth.get_access_token()
            url = f"{self.amadeus_auth.base_url}/v1/reference-data/locations"

            headers: Dict[str, str] = {"Authorization": f"Bearer {token}"}
            params: Dict[str, str | int] = {
                "keyword": keyword.strip(),
                "subType": subType.upper(),
                "view": "FULL",
                "page[limit]": 1,
            }

            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            if not data.get("data"):
                return None

            city_code = data["data"][0]["iataCode"]
            name = data["data"][0].get("name", keyword)

            return CitySearchResult(name=name, iata_code=city_code)

        except Exception as e:
            print(f"Tool Error for {keyword}: {e}")
            return None

    async def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async not supported yet")
