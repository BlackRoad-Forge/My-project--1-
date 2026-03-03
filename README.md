# Ollama Router

Route every `@copilot`, `@lucidia`, `@blackboxprogramming`, and `@ollama` mention
straight to your **local [Ollama](https://ollama.com/)** instance – no external
AI provider required.

## Recognised handles

| Handle | Destination |
|---|---|
| `@copilot` | Ollama (local) |
| `@lucidia` | Ollama (local) |
| `@blackboxprogramming` | Ollama (local) |
| `@ollama` | Ollama (local) |

## Requirements

* Python 3.10+
* [Ollama](https://ollama.com/) running locally (default: `http://localhost:11434`)

## Configuration

Edit `config.json` to change the Ollama URL or the default model:

```json
{
  "ollama": {
    "base_url": "http://localhost:11434",
    "default_model": "llama3"
  }
}
```

## CLI usage

```bash
python router.py "@ollama what is the capital of France?"
python router.py "@copilot explain async/await in Python"
python router.py "@blackboxprogramming show me the logs"
```

## Python API

```python
from router import OllamaRouter

router = OllamaRouter()

# Route only if a handle is present (returns None otherwise)
response = router.route("@ollama explain recursion")

# Always send to Ollama
response = router.chat("@copilot write a hello-world in Rust")
```

## Running tests

```bash
python -m unittest test_router -v
```
