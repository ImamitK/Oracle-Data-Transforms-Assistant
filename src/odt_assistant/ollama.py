"""Client for a locally running Ollama server."""

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .prompts import build_prompt
from .settings import Settings


class OllamaError(RuntimeError):
    """Raised when the local Ollama API cannot return a usable answer."""


class OllamaChat:
    def __init__(self, settings: Settings) -> None:
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model

    def ask(
        self,
        question: str,
        evidence: list[dict[str, str]] | None = None,
    ) -> tuple[str, dict[str, int]]:
        system_instruction, user_message = build_prompt(question, evidence)
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_message},
            ],
            "stream": False,
            "options": {"num_predict": 300, "temperature": 0.0},
        }
        request = Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(request, timeout=180) as response:
                result = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise OllamaError(f"Ollama returned HTTP {exc.code}: {detail}") from exc
        except (URLError, TimeoutError) as exc:
            raise OllamaError(
                "Could not reach Ollama. Check that the odt-ollama Docker "
                "container is running and port 11434 is available."
            ) from exc
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise OllamaError("Ollama returned an invalid JSON response.") from exc

        answer = result.get("message", {}).get("content", "").strip()
        if not answer:
            raise OllamaError("Ollama returned no text content.")

        usage = {
            "inputTokens": result.get("prompt_eval_count", 0),
            "outputTokens": result.get("eval_count", 0),
        }
        return answer, usage
