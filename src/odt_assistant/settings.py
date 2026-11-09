"""Configuration for the selected local or hosted model provider."""

from dataclasses import dataclass
import os

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    model_provider: str
    aws_region: str | None
    model_id: str | None
    aws_profile: str | None
    ollama_base_url: str
    ollama_model: str


def load_settings() -> Settings:
    load_dotenv()

    provider = os.getenv("MODEL_PROVIDER", "bedrock").strip().lower()
    region = os.getenv("AWS_REGION", "").strip() or None
    model_id = os.getenv("BEDROCK_MODEL_ID", "").strip() or None
    profile = os.getenv("AWS_PROFILE", "").strip() or None
    ollama_base_url = (
        os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").strip().rstrip("/")
    )
    ollama_model = os.getenv("OLLAMA_MODEL", "qwen2.5:3b").strip()

    if provider not in {"bedrock", "ollama"}:
        raise ValueError("MODEL_PROVIDER must be either 'bedrock' or 'ollama'.")

    missing = []
    if provider == "bedrock" and not region:
        missing.append("AWS_REGION")
    if provider == "bedrock" and not model_id:
        missing.append("BEDROCK_MODEL_ID")
    if provider == "ollama" and not ollama_model:
        missing.append("OLLAMA_MODEL")

    if missing:
        names = ", ".join(missing)
        raise ValueError(
            f"Set the following values in your .env file: {names}. "
            "Set the required values for the selected model provider."
        )

    return Settings(
        model_provider=provider,
        aws_region=region,
        model_id=model_id,
        aws_profile=profile,
        ollama_base_url=ollama_base_url,
        ollama_model=ollama_model,
    )
