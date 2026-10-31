import time
from datetime import datetime

from strands import tool

from common.data import ATTRACTIONS, FORECASTS, RESTAURANTS


@tool
def current_time() -> str:
    """Get today's date, weekday and the current time. Use this whenever a request mentions
    "today", "this Saturday", "next week" and so on."""
    return datetime.now().strftime("%A, %Y-%m-%d %H:%M")


@tool
def get_weather(city: str, day: str) -> dict:
    """Get the weather forecast for a city.

    Args:
        city: City name, e.g. "Kyoto"
        day: a date (YYYY-MM-DD) or a weekday (e.g. "Saturday")
    """
    time.sleep(0.3)  # pretend this is a real API call
    return FORECASTS.get(city, {"temp_c": 25, "conditions": "clear"}) | {"city": city, "day": day}


@tool
def find_attractions(city: str, indoor_only: bool = False) -> list[dict]:
    """Find top attractions in a city.

    Args:
        city: City name
        indoor_only: Only return indoor attractions (useful when it rains)
    """
    time.sleep(0.3)
    return [a for a in ATTRACTIONS.get(city, []) if a["indoor"] or not indoor_only]


@tool
def find_restaurants(city: str, diet: str | None = None, step_free: bool = False) -> list[dict]:
    """Find restaurants in a city.

    Args:
        city: City name
        diet: Only places that suit this diet, e.g. "vegetarian" or "vegan"
        step_free: Only places without steps (for wheelchairs and strollers)
    """
    time.sleep(0.3)
    places = RESTAURANTS.get(city, [])
    return [r for r in places if (not diet or diet.lower() in r["diets"]) and (r["step_free"] or not step_free)]
