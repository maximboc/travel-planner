from langchain.tools import tool
from datetime import datetime
from langsmith import traceable


@tool
@traceable(run_type="tool", name="get_todays_date")
def get_todays_date() -> str:
    """
    Returns today's date in YYYY-MM-DD format.
    """
    print("Getting today's date...")
    return datetime.now().strftime("%Y-%m-%d")
