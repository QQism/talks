"""Provider setup lives here so section code only shows agent concepts.

Pick a provider with PROVIDER in `.env` (see `.env.example`):
  bedrock    AWS credentials (AWS_PROFILE / AWS_REGION), the default
  anthropic  ANTHROPIC_API_KEY (Claude Platform)
  openai     OPENAI_API_KEY
MODEL_ID overrides the provider's default model.
"""

import os

from dotenv import load_dotenv
from strands.models import Model

load_dotenv()

DEFAULT_MODEL_IDS = {
    "bedrock": "global.anthropic.claude-sonnet-5-5",
    "anthropic": "claude-sonnet-5-5",
    "openai": "gpt-5",
}
# Current Claude models reject `temperature` and fixed thinking budgets: they choose sampling themselves,
# and with adaptive thinking they decide how much to think.
THINKING = {"type": "adaptive", "display": "summarized"}  # without "display", the thinking text comes back empty


def get_model(thinking: bool = False) -> Model:
    """thinking=True turns on adaptive thinking (Claude only; ignored for OpenAI)."""
    provider = os.environ.get("PROVIDER", "bedrock").lower()
    if provider not in DEFAULT_MODEL_IDS:
        raise ValueError(f"PROVIDER must be one of {', '.join(DEFAULT_MODEL_IDS)}, got {provider!r}")
    model_id = os.environ.get("MODEL_ID") or DEFAULT_MODEL_IDS[provider]

    if provider == "anthropic":
        from strands.models.anthropic import AnthropicModel

        return AnthropicModel(
            client_args={"api_key": os.environ["ANTHROPIC_API_KEY"]},
            model_id=model_id,
            max_tokens=8192,
            params={"thinking": THINKING} if thinking else {},
        )

    if provider == "openai":
        from strands.models.openai import OpenAIModel

        return OpenAIModel(
            client_args={"api_key": os.environ["OPENAI_API_KEY"]},
            model_id=model_id,
        )

    import boto3
    from strands.models import BedrockModel

    session = boto3.Session(
        profile_name=os.environ.get("AWS_PROFILE"),
        region_name=os.environ.get("AWS_REGION", "us-west-2"),
    )
    return BedrockModel(
        boto_session=session,
        model_id=model_id,
        max_tokens=8192,
        additional_request_fields={"thinking": THINKING} if thinking else None,
        # Some roles allow Converse but not ConverseStream; set BEDROCK_STREAMING=false for those.
        streaming=os.environ.get("BEDROCK_STREAMING", "true").lower() != "false",
    )
