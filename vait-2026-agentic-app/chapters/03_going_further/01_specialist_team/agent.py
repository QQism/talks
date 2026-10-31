from pathlib import Path

from strands import Agent
from strands.multiagent import GraphBuilder
from strands.vended_plugins.skills import AgentSkills

from common.model import get_model

from .tools import current_time, find_attractions, find_restaurants, get_weather, search_flights, search_hotels

SKILLS_DIR = Path(__file__).parent / "skills"


def specialist(name: str, job: str, tools: list, skills: tuple[str, ...] = (), **kwargs) -> Agent:
    return Agent(
        name=name,
        model=get_model(),
        system_prompt=f"You are the {name} specialist of a trip-planning team. {job}",
        tools=tools,
        # each specialist gets only the skills its job needs
        plugins=[AgentSkills(skills=[SKILLS_DIR / skill for skill in skills])] if skills else [],
        **kwargs,
    )


REPORT = "Use your tools, never guess. Reply with at most 5 short bullets for the writer."


def build_agent(**kwargs):
    # A team instead of one agent: three specialists work in parallel,
    # then the writer combines their findings into one plan.
    flights = specialist("flights", f"Find the best flight. {REPORT}", [current_time, search_flights], **kwargs)
    hotels = specialist("hotels", f"Find one hotel per city. {REPORT}", [search_hotels], ("accessible-travel",), **kwargs)
    activities = specialist(
        "activities", f"Plan what to do and where to eat each day. {REPORT}",
        [current_time, get_weather, find_attractions, find_restaurants], ("dietary-needs", "accessible-travel"), **kwargs,
    )
    writer = specialist(
        "writer",
        "Combine the team's findings into one short day-by-day plan for the travellers. Keep it under 200 words.",
        [],
        ("trip-planner",),
        **kwargs,
    )

    builder = GraphBuilder()
    for agent in (flights, hotels, activities, writer):
        builder.add_node(agent, agent.name)
    for node in ("flights", "hotels", "activities"):
        builder.set_entry_point(node)  # entry points start at the same time
        builder.add_edge(node, "writer")  # the writer waits for all three
    builder.set_execution_timeout(120)  # a safety net: stop the team after 2 minutes
    return builder.build()
