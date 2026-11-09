"""Answer a documentation question using retrieval and a selected model."""

import argparse
import sys

from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError

from .bedrock import BedrockChat
from .ollama import OllamaChat, OllamaError
from .retrieval import retrieve
from .settings import load_settings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Answer Oracle Data Transforms questions using documentation "
            "and a local Ollama or Amazon Bedrock model."
        )
    )
    parser.add_argument("question", nargs="+", help="Question about Oracle Data Transforms")
    args = parser.parse_args()
    question = " ".join(args.question).strip()

    # retrieve(question) searches the local chunk JSON before loading model settings or creating a provider client.
    # If no chunks match, the program prints that it found no passage and makes no model request.
    try:
        results = retrieve(question)
    except FileNotFoundError as exc:
        print(f"Documentation chunks are missing: {exc}", file=sys.stderr)
        return 2

    if not results:
        print(
            "I couldn't find a matching passage in the processed Oracle "
            "documentation. No model request was made."
        )
        return 0

    evidence = [
        {
            "source_url": result["chunk"]["source_url"],
            "text": result["chunk"]["text"],
        }
        for result in results
    ]

    # If chunks do match, their text and URLs become evidence, which is passed into chat.ask().
    try:
        settings = load_settings()
        if settings.model_provider == "ollama":
            chat = OllamaChat(settings)
        else:
            chat = BedrockChat(settings)
        answer, usage = chat.ask(question, evidence=evidence)
    except ValueError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2
    except NoCredentialsError:
        print(
            "AWS credentials were not found. Configure a local AWS profile or "
            "another supported boto3 credential source.",
            file=sys.stderr,
        )
        return 2
    except OllamaError as exc:
        print(f"Local model request failed: {exc}", file=sys.stderr)
        return 1
    except ClientError as exc:
        error = exc.response.get("Error", {})
        code = error.get("Code", "Unknown")
        message = error.get("Message", "No details provided")
        print(f"Bedrock request failed ({code}): {message}", file=sys.stderr)
        print(
            "Check the model ID, Region, model access, and "
            "bedrock:InvokeModel permission.",
            file=sys.stderr,
        )
        return 1
    except BotoCoreError as exc:
        print(f"AWS SDK request failed: {exc}", file=sys.stderr)
        return 1

    print(answer)

    # Show links taken directly from retrieved chunks.
    sources = sorted({item["source_url"] for item in evidence})
    print("\nRetrieved sources:")
    for source in sources:
        print(f"- {source}")

    if usage:
        print(
            "\nToken usage: "
            f"input={usage.get('inputTokens', 'unknown')}, "
            f"output={usage.get('outputTokens', 'unknown')}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
