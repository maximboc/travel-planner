from langchain.tools import tool, ToolRuntime
import requests
import os
from dotenv import load_dotenv

load_dotenv()


def convert_messages(runtime: ToolRuntime):
    messages = runtime.state["messages"]

    human_msgs = sum(1 for m in messages if m.__class__.__name__ == "HumanMessage")
    ai_msgs = sum(1 for m in messages if m.__class__.__name__ == "AIMessage")
    tool_msgs = sum(1 for m in messages if m.__class__.__name__ == "ToolMessage")
    return human_msgs, ai_msgs, tool_msgs


@tool
def find_place_details(query: str) -> str:
    """
    Searches for locations using OpenStreetMap.

    IMPORTANT: This tool works best with specific categories + city names.
    Examples of good queries:
    - "Beaches in Nice, France"
    - "Art Museums in Tokyo"
    - "Eiffel Tower, Paris"

    Args:
        query: The search string. Combine the category and the city (e.g., 'Parks in London').

    Returns:
        A formatted string of the top 3 matching locations with coordinates.
    """
    try:
        headers = {"User-Agent": "LangChainTravelAgent/1.0"}  # Updated User-Agent
        url = "https://nominatim.openstreetmap.org/search"

        params = {
            "q": query.strip(),
            "format": "jsonv2",
            "addressdetails": 1,
            "limit": 3,
        }

        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data:
            return f"No results found for '{query}'. Try a broader category (e.g., 'Museums' instead of 'Modern Art')."

        results = []
        for i, item in enumerate(data, 1):
            name = item.get("display_name", "N/A").split(",")[0]  # Clean up name
            full_address = item.get("display_name", "N/A")
            osm_type = item.get("type", "N/A")
            lat = item.get("lat", "N/A")
            lon = item.get("lon", "N/A")

            results.append(
                f"Place {i}: {name}\n"
                f"Type: {osm_type}\n"
                f"Full Address: {full_address}\n"
                f"Coords: {lat}, {lon}"
            )

        return "\n---\n".join(results)

    except Exception as e:
        return f"Error searching map: {str(e)}"


@tool
def get_exchange_rate(from_currency: str, to_currency: str) -> str:
    """
    Get the current exchange rate between two currencies.

    This tool helps travel agents provide accurate pricing in the user's preferred currency.
    It fetches real-time exchange rates from a free API.

    Args:
        from_currency: The source currency code (e.g., 'USD', 'EUR', 'GBP')
        to_currency: The target currency code (e.g., 'USD', 'EUR', 'GBP')

    Returns:
        A string containing the exchange rate and conversion information.

    Example:
        get_exchange_rate('USD', 'EUR') -> "1 USD = 0.92 EUR. Exchange rate: 0.92"
    """
    try:
        # Convert to uppercase to handle various input formats
        from_currency = from_currency.upper().strip()
        to_currency = to_currency.upper().strip()

        # Use Frankfurter API - free, no API key required
        url = f"https://api.frankfurter.dev/v1/latest?base={from_currency}&symbols={to_currency}"

        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()

        # Check if conversion was successful
        if "rates" not in data or to_currency not in data["rates"]:
            return f"Error: Unable to convert from '{from_currency}' to '{to_currency}'. Please use valid ISO currency codes."

        rate = data["rates"][to_currency]

        # Format the response with useful information
        result = (
            f"Exchange Rate: 1 {from_currency} = {rate:.4f} {to_currency}\n"
            f"To convert {from_currency} to {to_currency}, multiply by {rate:.4f}\n"
            f"Example: 100 {from_currency} = {(100 * rate):.2f} {to_currency}"
        )

        return result

    except requests.exceptions.RequestException as e:
        return f"Error fetching exchange rate: Unable to connect to exchange rate service. {str(e)}"
    except KeyError:
        return f"Error: Currency code '{from_currency}' not found. Please use valid ISO currency codes (e.g., USD, EUR, GBP, JPY)."
    except Exception as e:
        return f"Error getting exchange rate: {str(e)}"


@tool
def get_weather(city: str) -> str:
    """
    Get current weather information for a city.

    This tool helps travel agents provide weather information to users planning trips.
    It fetches real-time weather data from WeatherAPI.com.

    Args:
        city: The name of the city (e.g., 'London', 'Paris', 'New York')

    Returns:
        A string containing current weather information including temperature, conditions, and humidity.

    Example:
        get_weather('Paris') -> "Weather in Paris, FR: Clear sky, Temperature: 18°C (64°F)..."
    """
    try:
        # Get API key from parameter or environment variable
        api_key = os.getenv("WEATHER_API_KEY")

        if not api_key:
            return (
                "Error: WeatherAPI key not found. "
                "Please provide an API key or set the WEATHER_API_KEY environment variable."
            )

        # Clean city name
        city = city.strip()

        # Use WeatherAPI.com Current Weather API
        url = "https://api.weatherapi.com/v1/current.json"
        params = {
            "key": api_key,
            "q": city,
            "aqi": "no",  # Don't include air quality data
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        # Extract relevant weather information
        location = data["location"]
        current = data["current"]

        city_name = location["name"]
        country = location["country"]
        temp_celsius = current["temp_c"]
        temp_fahrenheit = current["temp_f"]
        feels_like_c = current["feelslike_c"]
        feels_like_f = current["feelslike_f"]
        humidity = current["humidity"]
        description = current["condition"]["text"]
        wind_kph = current["wind_kph"]
        wind_mph = current["wind_mph"]

        # Format the response
        result = (
            f"Weather in {city_name}, {country}:\n"
            f"Conditions: {description}\n"
            f"Temperature: {temp_celsius:.1f}°C ({temp_fahrenheit:.1f}°F)\n"
            f"Feels like: {feels_like_c:.1f}°C ({feels_like_f:.1f}°F)\n"
            f"Humidity: {humidity}%\n"
            f"Wind: {wind_kph:.1f} km/h ({wind_mph:.1f} mph)\n"
            f"This information helps plan appropriate clothing and activities for the trip."
        )

        return result

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401 or e.response.status_code == 403:
            return "Error: Invalid API key. Please check your WeatherAPI key."
        elif e.response.status_code == 400:
            try:
                error_data = e.response.json()
                error_msg = error_data.get("error", {}).get("message", "Bad request")
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


if __name__ == "__main__":
    print(get_exchange_rate("USD", "EUR"))
    print("\n")
    # print(get_weather("Tokyo"))
