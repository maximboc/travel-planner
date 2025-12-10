import requests
from typing import TypedDict, List, Tuple, Dict, Set
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

            url = f"https://api.frankfurter.dev/v1/latest?from={from_currency}&to={to_currency}"

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


def get_exchange_rates(
    conversion_requests: Set[Tuple[str, str]]
) -> Dict[Tuple[str, str], float]:
    """
    Fetches exchange rates for a set of currency conversion requests, batching API calls by the 'from' currency.

    Args:
        conversion_requests: A set of tuples, where each tuple is (from_currency, to_currency).

    Returns:
        A dictionary mapping each (from_currency, to_currency) tuple to its exchange rate.
    """
    rates: Dict[Tuple[str, str], float] = {}
    
    # Group requests by from_currency
    grouped_requests: Dict[str, List[str]] = {}
    for from_curr, to_curr in conversion_requests:
        if from_curr not in grouped_requests:
            grouped_requests[from_curr] = []
        grouped_requests[from_curr].append(to_curr)

    # Make one API call per from_currency
    for from_curr, to_currencies in grouped_requests.items():
        to_symbols = ",".join(set(to_currencies))
        url = f"https://api.frankfurter.dev/v1/latest?from={from_curr}&to={to_symbols}"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if "rates" in data:
                for to_curr, rate in data["rates"].items():
                    rates[(from_curr, to_curr)] = rate
        except Exception as e:
            print(f"   ⚠️ Could not fetch rates for {from_curr}: {e}")
            # On failure, assume a 1.0 rate for requested conversions from this base
            for to_curr in to_currencies:
                if (from_curr, to_curr) not in rates:
                    rates[(from_curr, to_curr)] = 1.0

    return rates
