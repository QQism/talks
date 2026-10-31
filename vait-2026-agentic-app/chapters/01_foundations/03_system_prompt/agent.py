from strands import Agent

from common.model import get_model

SYSTEM_PROMPT = """You are a friendly personal assistant.
Keep answers short: at most 5 bullet points."""


def build_agent(**kwargs) -> Agent:
    # The agent keeps the conversation in agent.messages
    # and sends all of it to the model on every call.
    return Agent(model=get_model(), system_prompt=SYSTEM_PROMPT, **kwargs)


if __name__ == "__main__":
    agent = build_agent()
    while True:
        agent(input("\n> "))
