"""
test_toolchain.py — Regression tests for toolchain.py

Uses the real core.py prompt/context machinery with a mocked Llama backend so
Core Protocol integration bugs are caught without loading a real model.
Run with: python test_toolchain.py
"""

import importlib.util
import json
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


# Mock llama_cpp before importing core.py.
class MockLlama:
    def __init__(self, model_path=None, n_ctx=None, **kwargs):
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.kwargs = kwargs
        self.last_prompt = None
        self.last_call_kwargs = None
        self.metadata = {}

    def tokenize(self, text, add_bos=True, special=False):
        return [ord(c) for c in text.decode("utf-8")]

    def close(self):
        pass

    def __call__(self, prompt, max_tokens=100, temperature=1.0, **kwargs):
        self.last_prompt = prompt
        self.last_call_kwargs = {
            "max_tokens": max_tokens,
            "temperature": temperature,
            **kwargs,
        }
        return {"choices": [{"text": MOCK_MODEL_OUTPUT}]}


mock_llama_cpp = types.ModuleType("llama_cpp")
setattr(mock_llama_cpp, "Llama", MockLlama)
sys.modules["llama_cpp"] = mock_llama_cpp

# Import the real core.py exactly as test_core.py does.
with patch("os.listdir", return_value=["model.gguf"]):
    import core

BASIC_RESPONSE = "I'm a helpful assistant."
MOCK_MODEL_OUTPUT = (
    "This is a thought.\n"
    + core.THINK_END
    + "\n"
    + BASIC_RESPONSE
)

core.DISPLAY_EXTENDED_REASONING = True

# toolchain.py imports comms and codex, but these tests do not need their external
# dependencies. Load toolchain under a private module name with tiny stubs while
# keeping the real core module above.
mock_comms = types.ModuleType("comms")
setattr(mock_comms, "printSystemText", lambda text: None)
setattr(mock_comms, "printMagiText", lambda text: None)

mock_codex = types.ModuleType("codex")
setattr(mock_codex, "read_codex", lambda action: "")
setattr(mock_codex, "delete_codex", lambda action: "")
setattr(mock_codex, "write_codex", lambda action: "")

toolchain_path = Path(__file__).resolve().parent.parent / "toolchain.py"
spec = importlib.util.spec_from_file_location("_toolchain_under_test", toolchain_path)
toolchain = importlib.util.module_from_spec(spec)

with patch.dict(sys.modules, {"comms": mock_comms, "codex": mock_codex}):
    spec.loader.exec_module(toolchain)


PRIME_DIRECTIVES = "You are a friendly AI assistant."
ACTION = "Review the production code carefully."
CORE_PROTOCOL = "\n---\nFollow the Core Protocol exactly."
NORMAL_RESPONSE = core.THINK_TRIGGER + MOCK_MODEL_OUTPUT


class TestCoreProtocolIntegration(unittest.TestCase):
    def setUp(self):
        core.model = MockLlama(model_path="model.gguf", n_ctx=core.CONTEXT_SIZE)
        toolchain.CORE_PROTOCOL = CORE_PROTOCOL
        toolchain.TOOLS.clear()
        toolchain.codex_enabled = False

    def test_core_protocol_is_used_for_inference_but_not_stored(self):
        context = []

        response = toolchain.run_core_protocol(PRIME_DIRECTIVES, ACTION, context)

        self.assertEqual(response, NORMAL_RESPONSE)
        self.assertIn(ACTION + CORE_PROTOCOL, core.model.last_prompt)
        self.assertEqual(
            context[1],
            core.USER_TEXT + ACTION + core.EOS + core.ASSISTANT_TEXT,
        )
        self.assertNotIn(CORE_PROTOCOL, context[1])

    def test_assistant_template_newline_is_preserved(self):
        context = []

        toolchain.run_core_protocol(PRIME_DIRECTIVES, ACTION, context)

        self.assertTrue(context[1].endswith(core.EOS + core.ASSISTANT_TEXT))

    def test_action_literal_core_protocol_is_preserved(self):
        action = "Literal protocol follows:" + CORE_PROTOCOL + "\nKeep this literal copy."
        context = []

        toolchain.run_core_protocol(PRIME_DIRECTIVES, action, context)

        self.assertEqual(context[1].count(CORE_PROTOCOL), 1)
        self.assertIn(action, context[1])

    def test_multiple_action_literal_protocols_are_preserved(self):
        action = "A" + CORE_PROTOCOL + "\nB" + CORE_PROTOCOL + "\nC"
        context = []

        toolchain.run_core_protocol(PRIME_DIRECTIVES, action, context)

        self.assertEqual(context[1].count(CORE_PROTOCOL), 2)
        self.assertIn(action, context[1])

    def test_trailing_action_whitespace_is_not_stripped_by_cleanup(self):
        action = "Keep trailing whitespace   \n\n"
        context = []

        toolchain.run_core_protocol(PRIME_DIRECTIVES, action, context)

        self.assertEqual(
            context[1],
            core.USER_TEXT + action + core.EOS + core.ASSISTANT_TEXT,
        )

    def test_empty_core_protocol_is_safe(self):
        toolchain.CORE_PROTOCOL = ""
        context = []

        toolchain.run_core_protocol(PRIME_DIRECTIVES, ACTION, context)

        self.assertEqual(
            context[1],
            core.USER_TEXT + ACTION + core.EOS + core.ASSISTANT_TEXT,
        )

    def test_existing_context_is_not_modified(self):
        context = [
            core.SYSTEM_TEXT + "Old directives" + core.EOS,
            core.USER_TEXT + "Old action" + core.EOS + core.ASSISTANT_TEXT,
            "Old response" + core.EOS,
        ]
        old_turn = context[1:].copy()

        toolchain.run_core_protocol(PRIME_DIRECTIVES, ACTION, context)

        self.assertEqual(context[1:3], old_turn)
        self.assertEqual(
            context[3],
            core.USER_TEXT + ACTION + core.EOS + core.ASSISTANT_TEXT,
        )

    def test_hide_reasoning_is_forwarded(self):
        context = []

        response = toolchain.run_core_protocol(
            PRIME_DIRECTIVES,
            ACTION,
            context,
            hide_reasoning=True,
        )

        self.assertEqual(response, BASIC_RESPONSE)
        self.assertEqual(context[2], BASIC_RESPONSE + core.EOS)

    def test_repeated_calls_keep_valid_context_structure(self):
        context = []

        toolchain.run_core_protocol(PRIME_DIRECTIVES, "First action", context)
        toolchain.run_core_protocol(PRIME_DIRECTIVES, "Second action", context)

        self.assertEqual(len(context), 5)
        self.assertEqual(
            context[1],
            core.USER_TEXT + "First action" + core.EOS + core.ASSISTANT_TEXT,
        )
        self.assertEqual(
            context[3],
            core.USER_TEXT + "Second action" + core.EOS + core.ASSISTANT_TEXT,
        )


    def test_empty_action_does_nothing(self):
        context = []

        response = toolchain.run_core_protocol(PRIME_DIRECTIVES, "", context)

        self.assertEqual(response, "")
        self.assertEqual(context, [])
        self.assertIsNone(core.model.last_prompt)

    def test_whitespace_only_action_does_nothing(self):
        context = []

        response = toolchain.run_core_protocol(PRIME_DIRECTIVES, "   \n\t", context)

        self.assertEqual(response, "")
        self.assertEqual(context, [])
        self.assertIsNone(core.model.last_prompt)


class TestRunActionIntegration(unittest.TestCase):
    def setUp(self):
        core.model = MockLlama(model_path="model.gguf", n_ctx=core.CONTEXT_SIZE)
        toolchain.CORE_PROTOCOL = CORE_PROTOCOL
        toolchain.TOOLS.clear()
        toolchain.codex_enabled = False

    def test_run_action_without_tools_uses_core_protocol_pipeline(self):
        context = []

        response = toolchain.runAction(PRIME_DIRECTIVES, ACTION, context)

        self.assertEqual(response, BASIC_RESPONSE)
        self.assertEqual(
            context[1],
            core.USER_TEXT + ACTION + core.EOS + core.ASSISTANT_TEXT,
        )
        self.assertNotIn(CORE_PROTOCOL, context[1])

    def test_empty_actions_do_nothing_before_codex_tools_or_output(self):
        tool_calls = []

        def sample_tool(prime: str, action: str, context: list[str]) -> str:
            tool_calls.append((prime, action, context))
            return "done"

        toolchain.add_tool("sample", "Sample", sample_tool)
        toolchain.codex_enabled = True

        for action in ("", "   \n\t"):
            with self.subTest(action=repr(action)):
                context = []

                with (
                    patch.object(toolchain.codex, "read_codex") as mock_read,
                    patch.object(core, "send_prompt") as mock_send,
                    patch.object(toolchain.comms, "printMagiText") as mock_print,
                ):
                    response = toolchain.runAction(PRIME_DIRECTIVES, action, context)

                self.assertEqual(response, "")
                self.assertEqual(context, [])
                self.assertEqual(tool_calls, [])
                mock_read.assert_not_called()
                mock_send.assert_not_called()
                mock_print.assert_not_called()


class TestToolRegistrationAndDispatch(unittest.TestCase):
    def setUp(self):
        toolchain.TOOLS.clear()

    def test_add_and_print_tool(self):
        def sample_tool(prime: str, action: str, context: list[str]) -> str:
            return action

        toolchain.add_tool("Sample_Tool", "Sample description", sample_tool)
        data = json.loads(toolchain.print_tools())

        self.assertEqual(
            data,
            [{"name": "sample_tool", "description": "Sample description"}],
        )

    def test_duplicate_tool_is_rejected(self):
        def sample_tool(prime: str, action: str, context: list[str]) -> str:
            return action

        toolchain.add_tool("sample", "Sample", sample_tool)

        with self.assertRaises(ValueError):
            toolchain.add_tool("sample", "Sample", sample_tool)

    def test_invalid_signature_is_rejected(self):
        def bad_tool(prime: str, action: str) -> str:
            return action

        with self.assertRaises(ValueError):
            toolchain.add_tool("bad", "Bad", bad_tool)

    def test_run_tool_forwards_optional_is_agent(self):
        received = []

        def sample_tool(
            prime: str,
            action: str,
            context: list[str],
            is_agent: bool,
        ) -> str:
            received.append((prime, action, context, is_agent))
            return "done"

        toolchain.add_tool("sample", "Sample", sample_tool)
        context = ["context"]

        result = toolchain.run_tool("sample", "prime", "action", context, True)

        self.assertEqual(result, "done")
        self.assertEqual(received, [("prime", "action", context, True)])


if __name__ == "__main__":
    unittest.main(verbosity=2)

