import asyncio
from pathlib import Path

from strands import Agent
from strands.vended_plugins.skills import AgentSkills

from common.model import get_model

from .models import Itinerary
from .tools import current_time, find_attractions, find_restaurants, get_weather

SKILLS_DIR = Path(__file__).parent / "skills"

SYSTEM_PROMPT = """You are a friendly personal assistant.
Use your tools for dates, weather, attractions and restaurants. Never guess.
Always answer by calling the Itinerary tool. Don't ask questions: if details are missing,
assume something sensible and say so in the tips."""


def build_agent(**kwargs) -> Agent:
    # The agent keeps the conversation in agent.messages
    # and sends all of it to the model on every call.
    return Agent(
        model=get_model(thinking=True),  # the model reasons before it answers
        system_prompt=SYSTEM_PROMPT,
        tools=[current_time, get_weather, find_attractions, find_restaurants],
        plugins=[AgentSkills(skills=[SKILLS_DIR])],  # loads a skill only when it's relevant
        structured_output_model=Itinerary,  # answer with data the app can render, not prose
        **kwargs,
    )


async def chat(agent: Agent, prompt: str) -> None:
    # Print the finished itinerary as JSON once the agent is done.
    async for event in agent.stream_async(prompt):
        if "result" in event:
            itinerary: Itinerary = event["result"].structured_output
            print(itinerary.model_dump_json(indent=2))


if __name__ == "__main__":
    agent = build_agent(callback_handler=None)
    while True:
        asyncio.run(chat(agent, input("\n> ")))
