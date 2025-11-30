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
            from_currency = from_currency.upper().strip()
            to_currency = to_currency.upper().strip()

            url = f"https://api.frankfurter.dev/v1/latest?base={from_currency}&symbols={to_currency}"

            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()

            if "rates" not in data or to_currency not in data["rates"]:
                raise ValueError(
                    f"Exchange rate data not available for {from_currency} to {to_currency}."
                )

            rate = data["rates"][to_currency]

            return ExchangeRateResult(
                rate=rate,
                from_currency=from_currency,
                to_currency=to_currency,
            )

        except Exception as e:
            raise ValueError(f"Error fetching exchange rate: {str(e)}")

    async def _arun(self, from_currency: str, to_currency: str) -> ExchangeRateResult:
        raise NotImplementedError("get_exchange_rate does not support async")
