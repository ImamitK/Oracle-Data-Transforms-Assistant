"""Minimal Amazon Bedrock Converse client."""

import boto3

from .settings import Settings
from .prompts import build_prompt


class BedrockChat:
    def __init__(self, settings: Settings) -> None:
        if not settings.aws_region or not settings.model_id:
            raise ValueError(
                "AWS_REGION and BEDROCK_MODEL_ID are required for Bedrock."
            )
        if settings.aws_profile:
            session = boto3.Session(profile_name=settings.aws_profile)
        else:
            session = boto3.Session()

        self.client = session.client(
            service_name="bedrock-runtime",
            region_name=settings.aws_region,
        )
        self.model_id = settings.model_id

    def ask(
        self,
        question: str,
        evidence: list[dict[str, str]] | None = None,
    ) -> tuple[str, dict]:
        system_instruction, user_message = build_prompt(question, evidence)

        response = self.client.converse(
            modelId=self.model_id,
            system=[{"text": system_instruction}],
            messages=[
                {
                    "role": "user",
                    "content": [{"text": user_message}],
                }
            ],
            inferenceConfig={"maxTokens": 300},
        )

        content = response.get("output", {}).get("message", {}).get("content", [])
        answer = "\n".join(block["text"] for block in content if "text" in block)
        if not answer:
            raise RuntimeError("Bedrock returned no text content.")

        return answer, response.get("usage", {})
