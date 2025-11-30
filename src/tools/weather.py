from typing import TypedDict
import os
import requests
from langsmith import traceable
from langchain.tools import BaseTool


class WeatherToolResult(TypedDict):
    """Custom exception for weather tool errors."""

    city_name: str
    country: str
    temp_c: float
    temp_f: float
    feels_like_c: float
    feels_like_f: float
    condition: str
    humidity: int
    wind_kph: float
    wind_mph: float


class GetWeatherTool(BaseTool):
    name: str = "get_weather"
    description: str = (
        "Get current weather information for a city. "
        "This tool helps travel agents provide weather information to users planning trips. "
        "It fetches real-time weather data from WeatherAPI.com."
    )

    @traceable(run_type="tool", name=name)
    def _run(self, city: str) -> WeatherToolResult:
        """
        Get current weather information for a city.

        Args:
            city: The name of the city (e.g., 'London', 'Paris', 'New York')

        Returns:
            A string containing current weather information including temperature, conditions, and humidity.
        """
        try:
            api_key = os.getenv("WEATHER_API_KEY")

            if not api_key:
                raise ValueError("WEATHER_API_KEY environment variable is not set.")

            city = city.strip()

            url = "https://api.weatherapi.com/v1/current.json"
            params = {
                "key": api_key,
                "q": city,
                "aqi": "no",
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            location = data["location"]
            current = data["current"]

            # Format the response
            result = WeatherToolResult(
                city_name=location["name"],
                country=location["country"],
                temp_c=current["temp_c"],
                temp_f=current["temp_f"],
                feels_like_c=current["feelslike_c"],
                feels_like_f=current["feelslike_f"],
                condition=current["condition"]["text"],
                humidity=current["humidity"],
                wind_kph=current["wind_kph"],
                wind_mph=current["wind_mph"],
            )

            return result

        except requests.exceptions.HTTPError as e:
            raise ValueError(f"HTTP error occurred: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Error: Unable to connect to weather service. {str(e)}")
        except KeyError as e:
            raise ValueError(
                f"Error: Unexpected response format from weather service. Missing key: {str(e)}"
            )
        except Exception as e:
            raise ValueError(f"Error getting weather: {str(e)}")

    async def _arun(self, city: str) -> WeatherToolResult:
        raise NotImplementedError("Async execution is not supported for this tool.")
