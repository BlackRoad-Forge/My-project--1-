"""Tests for the Ollama router."""

import json
import sys
import unittest
from unittest.mock import MagicMock, patch

# Make the project root importable
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))

from router import OllamaRouter, _HANDLE_PATTERN


class TestHandleDetection(unittest.TestCase):
    """OllamaRouter.contains_handle / strip_handle"""

    def test_copilot_detected(self):
        self.assertTrue(OllamaRouter.contains_handle("@copilot help me"))

    def test_lucidia_detected(self):
        self.assertTrue(OllamaRouter.contains_handle("@lucidia explain this"))

    def test_blackboxprogramming_detected(self):
        self.assertTrue(OllamaRouter.contains_handle("@blackboxprogramming run a query"))

    def test_ollama_detected(self):
        self.assertTrue(OllamaRouter.contains_handle("@ollama what is 2+2?"))

    def test_case_insensitive(self):
        self.assertTrue(OllamaRouter.contains_handle("@Copilot help"))
        self.assertTrue(OllamaRouter.contains_handle("@OLLAMA help"))

    def test_unknown_handle_not_detected(self):
        self.assertFalse(OllamaRouter.contains_handle("@openai help"))

    def test_no_handle_not_detected(self):
        self.assertFalse(OllamaRouter.contains_handle("just a plain message"))

    def test_strip_handle_copilot(self):
        self.assertEqual(OllamaRouter.strip_handle("@copilot what is Python?"), "what is Python?")

    def test_strip_handle_ollama(self):
        self.assertEqual(OllamaRouter.strip_handle("@ollama explain recursion"), "explain recursion")

    def test_strip_handle_preserves_rest(self):
        result = OllamaRouter.strip_handle("@blackboxprogramming show me the logs")
        self.assertEqual(result, "show me the logs")


class TestRouteMethod(unittest.TestCase):
    """OllamaRouter.route returns None for unknown handles."""

    def test_route_returns_none_for_unknown_handle(self):
        router = OllamaRouter()
        self.assertIsNone(router.route("@openai do something"))

    def test_route_returns_none_for_plain_message(self):
        router = OllamaRouter()
        self.assertIsNone(router.route("no handle here"))


class TestChatForwardedToOllama(unittest.TestCase):
    """OllamaRouter.chat sends request to Ollama and returns response."""

    def _make_mock_response(self, response_text: str):
        body = json.dumps({"response": response_text}).encode()
        mock_resp = MagicMock()
        mock_resp.read.return_value = body
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        return mock_resp

    @patch("urllib.request.urlopen")
    def test_chat_sends_prompt_to_ollama(self, mock_urlopen):
        mock_urlopen.return_value = self._make_mock_response("Paris")
        router = OllamaRouter(base_url="http://localhost:11434", model="llama3")
        result = router.chat("@ollama what is the capital of France?")
        self.assertEqual(result, "Paris")
        # Verify the URL used
        call_args = mock_urlopen.call_args
        req = call_args[0][0]
        self.assertIn("/api/generate", req.full_url)

    @patch("urllib.request.urlopen")
    def test_chat_strips_handle_before_sending(self, mock_urlopen):
        mock_urlopen.return_value = self._make_mock_response("42")
        router = OllamaRouter(base_url="http://localhost:11434", model="llama3")
        router.chat("@copilot what is 6 times 7?")
        req = mock_urlopen.call_args[0][0]
        sent_payload = json.loads(req.data.decode())
        self.assertEqual(sent_payload["prompt"], "what is 6 times 7?")

    @patch("urllib.request.urlopen")
    def test_route_calls_ollama_for_recognised_handle(self, mock_urlopen):
        mock_urlopen.return_value = self._make_mock_response("Hello!")
        router = OllamaRouter(base_url="http://localhost:11434", model="llama3")
        result = router.route("@lucidia say hello")
        self.assertEqual(result, "Hello!")

    @patch("urllib.request.urlopen")
    def test_all_handles_reach_ollama(self, mock_urlopen):
        mock_urlopen.return_value = self._make_mock_response("ok")
        router = OllamaRouter(base_url="http://localhost:11434", model="llama3")
        for handle in ("@copilot", "@lucidia", "@blackboxprogramming", "@ollama"):
            mock_urlopen.reset_mock()
            mock_urlopen.return_value = self._make_mock_response("ok")
            result = router.route(f"{handle} test message")
            self.assertIsNotNone(result, f"{handle} should route to Ollama")
            self.assertTrue(mock_urlopen.called, f"{handle} should call Ollama API")


if __name__ == "__main__":
    unittest.main()
