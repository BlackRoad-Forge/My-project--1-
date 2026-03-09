"""
Ollama Router – all @handles route to your local Ollama instance.

Recognised handles (case-insensitive):
  @copilot  @lucidia  @blackboxprogramming  @ollama

Usage
-----
Python API::

    from router import OllamaRouter
    router = OllamaRouter()
    response = router.chat("@ollama what is the capital of France?")

CLI::

    python router.py "@ollama what is the capital of France?"
"""

import json
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path

# ---------------------------------------------------------------------------
# Handles that must be routed to Ollama
# ---------------------------------------------------------------------------
_HANDLE_PATTERN = re.compile(
    r"@(copilot|lucidia|blackboxprogramming|ollama)\b",
    re.IGNORECASE,
)

_CONFIG_PATH = Path(__file__).parent / "config.json"


def _load_config() -> dict:
    """Load config.json from the project root."""
    if _CONFIG_PATH.exists():
        with _CONFIG_PATH.open() as fh:
            return json.load(fh)
    return {
        "ollama": {"base_url": "http://localhost:11434", "default_model": "llama3"},
    }


class OllamaRouter:
    """Routes every recognised @handle to the local Ollama service."""

    def __init__(self, base_url: str | None = None, model: str | None = None):
        cfg = _load_config()
        ollama_cfg = cfg.get("ollama", {})
        self.base_url = (base_url or ollama_cfg.get("base_url", "http://localhost:11434")).rstrip("/")
        self.model = model or ollama_cfg.get("default_model", "llama3")

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    @staticmethod
    def contains_handle(message: str) -> bool:
        """Return True if *message* contains a recognised @handle."""
        return bool(_HANDLE_PATTERN.search(message))

    @staticmethod
    def strip_handle(message: str) -> str:
        """Remove leading @handle token(s) and return the clean prompt."""
        return _HANDLE_PATTERN.sub("", message).strip()

    def chat(self, message: str, model: str | None = None) -> str:
        """
        Send *message* to Ollama and return the response text.

        If *message* does not contain a recognised handle this method still
        forwards the request to Ollama – the caller is responsible for
        deciding whether to call this method.
        """
        prompt = self.strip_handle(message)
        payload = json.dumps(
            {
                "model": model or self.model,
                "prompt": prompt,
                "stream": False,
            }
        ).encode()

        url = f"{self.base_url}/api/generate"
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                body = json.loads(resp.read().decode())
                return body.get("response", "")
        except urllib.error.URLError as exc:
            raise ConnectionError(
                f"Could not reach Ollama at {self.base_url}. "
                "Make sure Ollama is running locally. "
                f"Original error: {exc}"
            ) from exc

    def route(self, message: str, model: str | None = None) -> str | None:
        """
        If *message* mentions a recognised @handle, forward to Ollama and
        return the response.  Otherwise return None so the caller can apply
        its own fallback logic.
        """
        if self.contains_handle(message):
            return self.chat(message, model=model)
        return None


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python router.py \"@ollama <your question>\"")
        sys.exit(1)

    message = " ".join(sys.argv[1:])
    router = OllamaRouter()

    if not router.contains_handle(message):
        print(
            "No recognised handle found in message.\n"
            "Recognised handles: @copilot, @lucidia, @blackboxprogramming, @ollama"
        )
        sys.exit(1)

    try:
        print(router.chat(message))
    except ConnectionError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
