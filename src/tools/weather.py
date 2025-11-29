from typing import TypedDict, ClassVar
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
    condition: str
    humidity: int
    wind_kph: float
    wind_mph: float


class GetWeatherTool(BaseTool):
    name: ClassVar[str] = "get_weather"
    description: ClassVar[str] = (
        "Get current weather information for a city. "
        "This tool helps travel agents provide weather information to users planning trips. "
        "It fetches real-time weather data from WeatherAPI.com."
    )

    @traceable(run_type="tool", name=name)
    def _run(self, city: str) -> str:
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
                return (
                    "Error: WeatherAPI key not found. "
                    "Please provide an API key or set the WEATHER_API_KEY environment variable."
                )

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
            if e.response.status_code == 401 or e.response.status_code == 403:
                return "Error: Invalid API key. Please check your WeatherAPI key."
            elif e.response.status_code == 400:
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get("error", {}).get(
                        "message", "Bad request"
                    )
                    return f"Error: {error_msg}"
                except:
                    return f"Error: City '{city}' not found or invalid request. Please check the spelling."
            else:
                return f"Error fetching weather data: HTTP {e.response.status_code}"
        except requests.exceptions.RequestException as e:
            return f"Error: Unable to connect to weather service. {str(e)}"
        except KeyError as e:
            return f"Error: Unexpected response format from weather service. Missing key: {str(e)}"
        except Exception as e:
            return f"Error getting weather: {str(e)}"

    async def _arun(self, city: str) -> str:
        raise NotImplementedError("Async execution is not supported for this tool.")
