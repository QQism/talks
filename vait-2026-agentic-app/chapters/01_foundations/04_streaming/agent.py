import asyncio

from strands import Agent

from common.model import get_model

SYSTEM_PROMPT = """You are a friendly personal assistant.
Keep answers short: at most 5 bullet points."""


def build_agent(**kwargs) -> Agent:
    # The agent keeps the conversation in agent.messages
    # and sends all of it to the model on every call.
    return Agent(model=get_model(), system_prompt=SYSTEM_PROMPT, **kwargs)


async def chat(agent: Agent, prompt: str) -> None:
    # Print each piece of text as soon as the model produces it.
    async for event in agent.stream_async(prompt):
        if "data" in event:
            print(event["data"], end="", flush=True)


if __name__ == "__main__":
    agent = build_agent(callback_handler=None)
    while True:
        asyncio.run(chat(agent, input("\n> ")))
