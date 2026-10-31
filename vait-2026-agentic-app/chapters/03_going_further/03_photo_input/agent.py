import asyncio
from pathlib import Path

from strands import Agent
from strands.vended_plugins.skills import AgentSkills

from common.model import get_model

from .tools import current_time, find_attractions, find_restaurants, get_weather

SKILLS_DIR = Path(__file__).parent / "skills"

SYSTEM_PROMPT = """You are a friendly personal assistant.
Keep answers short: at most 5 bullet points.
Use your tools for dates, weather, attractions and restaurants. Never guess."""


def build_agent(**kwargs) -> Agent:
    # The agent keeps the conversation in agent.messages
    # and sends all of it to the model on every call.
    return Agent(
        model=get_model(thinking=True),  # the model reasons before it answers
        system_prompt=SYSTEM_PROMPT,
        tools=[current_time, get_weather, find_attractions, find_restaurants],
        plugins=[AgentSkills(skills=[SKILLS_DIR])],  # loads a skill only when it's relevant
        **kwargs,
    )


async def chat(agent: Agent, prompt: str, photo: Path | None = None) -> None:
    # A message can mix text and images: the model sees both.
    content = [{"text": prompt}]
    if photo:
        content.append({"image": {"format": "jpeg", "source": {"bytes": photo.read_bytes()}}})
    # Print each piece of text as soon as the model produces it.
    async for event in agent.stream_async(content):
        if "reasoningText" in event:
            print(event["reasoningText"], end="", flush=True)  # thinking
        if "data" in event:
            print(event["data"], end="", flush=True)  # answer


if __name__ == "__main__":
    agent = build_agent(callback_handler=None)
    while True:
        prompt = input("\n> ")
        photo = input("photo path (optional)> ").strip()
        asyncio.run(chat(agent, prompt, Path(photo) if photo else None))
