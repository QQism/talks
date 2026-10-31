from pydantic import BaseModel, Field


class Stop(BaseModel):
    time: str = Field(description='Start time, e.g. "09:30"')
    name: str = Field(description="Place name, exactly as returned by find_attractions")
    why: str = Field(description="One sentence on why this stop suits the travellers")
    indoor: bool
    photo: str | None = Field(default=None, description="Photo id from find_attractions, if any")


class DayPlan(BaseModel):
    day: str = Field(description='e.g. "Saturday"')
    city: str
    weather: str = Field(description="Forecast summary from get_weather")
    stops: list[Stop]


class Itinerary(BaseModel):
    title: str
    travellers: str = Field(description='Who is travelling, e.g. "Quang, his wife and their two kids"')
    days: list[DayPlan]
    tips: list[str] = Field(description="At most 3 practical tips")
