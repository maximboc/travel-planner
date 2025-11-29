import requests
from typing import TypedDict
from langchain.tools import BaseTool


class ExchangeRateResult(TypedDict):
    """Custom exception for exchange rate tool errors."""

    rate: float
    from_currency: str
    to_currency: str


class GetExchangeRateTool(BaseTool):
    name: str = "get_exchange_rate"
    description: str = (
        "Get the current exchange rate between two currencies. "
        "This tool helps travel agents provide accurate pricing in the user's preferred currency."
    )

    def _run(self, from_currency: str, to_currency: str) -> ExchangeRateResult:
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

            return ExchangeRateResult(
                rate=rate,
                from_currency=from_currency,
                to_currency=to_currency,
            )

        except requests.exceptions.RequestException as e:
            return f"Error fetching exchange rate: Unable to connect to exchange rate service. {str(e)}"
        except KeyError:
            return f"Error: Currency code '{from_currency}' not found. Please use valid ISO currency codes (e.g., USD, EUR, GBP, JPY)."
        except Exception as e:
            return f"Error getting exchange rate: {str(e)}"

        async def _arun(
            self, from_currency: str, to_currency: str
        ) -> ExchangeRateResult:
            raise NotImplementedError("get_exchange_rate does not support async")
