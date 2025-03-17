import os
import requests
from typing import Any, Callable, Annotated
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg

from realzen_agent.utils.configuration import Configuration


@tool
def search_for_properties_by_location(
    location: str,
    config: Annotated[RunnableConfig, InjectedToolArg],
    types: tuple = ("isSingleFamily",),
    **kwargs: Any,
) -> list[dict[str, Any]]:
    """Search for properties listed on Zillow by location.
    By default, the function returns residential properties
    for sale listed by agent and sorted by newest
    listings first. To filter the results by property type,
    you can use the below optional keyword arguments.
    Args:
        location (str): The location to search for properties.
        e.g. "San Francisco, CA"
    Keyword Args:
    - types (typle): The types of property to search for.
        - isSingleFamily: Single-family homes
        - isMultiFamily: Multi-family homes
        - isCondo: Condos
        - isTownhouse: Townhouses
        - isApartment: Apartments
        - isLotLand: Land
        - isManufactured: Manufactured homes
    - limit (int): The maximum number of search results to return.
    Returns:
        list[dict[str, Any]]: The search results.
    """
    property_types = {
        "isSingleFamily": "false",
        "isMultiFamily": "false",
        "isCondo": "false",
        "isTownhouse": "false",
        "isApartment": "false",
        "isLotLand": "false",
        "isManufactured": "false",
    }
    for _type in types:
        property_types[_type] = "true"

    configuration = Configuration.from_runnable_config(config)
    limit = configuration.max_search_results

    url = "https://zillow56.p.rapidapi.com/search"
    querystring = {
        "location": location,
        "output": "json",
        **property_types,
        **kwargs,
    }

    headers = {
        "x-rapidapi-key": os.environ["RAPIDAPI_KEY"],
        "x-rapidapi-host": "zillow56.p.rapidapi.com",
    }

    response = requests.get(url, headers=headers, params=querystring)
    results = response.json()["results"][:limit]
    return results


@tool
def calculate_cash_on_cash(
    home_price: float,
    rent: float,
    tax_assessed_value: float,
    down_payment: float = 0.2,
    **kwargs: Any,
) -> float:
    """Calculate the cash-on-cash
    return on investment for a rental property.
    Args:
        home_price (float): The price of the home.
        rent (float): The monthly rent.
        tax_assessed_value (float): The tax-assessed value of the home.
    Keyword Args:
    - down_payment (float): The down payment as a percentage of the home price.
    Returns:
        float: The cash-on-cash return on investment.
    """
    interest_rate = 0.065 / 12  # National average 6.5%
    loan_term = 30  # 30-year fixed-rate mortgage

    down_payment_amount = home_price * down_payment  # 20% down payment
    loan_amount = home_price - down_payment_amount
    annual_property_tax = tax_assessed_value * 0.009  # National average 0.9%
    annual_mortgage_payment = (
        loan_amount
        * (interest_rate * (1 + interest_rate) ** (loan_term * 12))
        / ((1 + interest_rate) ** (loan_term * 12) - 1)
    ) * 12
    management_fee = rent * 0.1 * 12  # 10% of the monthly rent
    cash_flow = rent * 12
    cash_on_cash = (
        cash_flow - annual_property_tax - annual_mortgage_payment - management_fee
    ) / down_payment_amount
    return cash_on_cash


TOOLS: list[Callable[..., Any]] = [
    search_for_properties_by_location,
    calculate_cash_on_cash,
]

if __name__ == "__main__":
    from dotenv import load_dotenv
    import json

    load_dotenv()

    results = search_for_properties_by_location.invoke(
        "San Francisco, CA", types=("isSingleFamily"), limit=5
    )
    # print(results)
    with open("example_results.json", "w") as f:
        json.dump(results, f, indent=2)
