import anthropic
from dotenv import load_dotenv

load_dotenv()  # ANTHROPIC_API_KEY from .env

client = anthropic.Anthropic()
MODEL_ID = "claude-sonnet-5-5"


def ask(prompt: str) -> str:
    # One request, one response. Nothing is remembered between calls.
    response = client.messages.create(
        model=MODEL_ID,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in response.content if block.type == "text")


if __name__ == "__main__":
    while True:
        print(ask(input("\n> ")))
