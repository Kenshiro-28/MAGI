import unittest
import sys
import types
from unittest.mock import patch

# Create a mock for the Llama class that will be imported in core.py
class MockLlama:
    def __init__(self, model_path=None, n_ctx=None, **kwargs):
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.verbose = True
        self.kwargs = kwargs
        self.last_prompt = None
        self.last_call_kwargs = None
        self.metadata = {}

    def tokenize(self, text, add_bos = True, special = False):
        if special is not True:
            raise AssertionError("MockLlama.tokenize requires special=True")
        return [ord(c) for c in text.decode('utf-8')]

    def close(self):
        pass

    def __call__(self, prompt, max_tokens=100, temperature=1.0, **kwargs):
        self.last_prompt = prompt
        self.last_call_kwargs = {
            'max_tokens': max_tokens,
            'temperature': temperature,
            **kwargs
        }

        return {
            'choices': [
                {'text': MOCK_MODEL_OUTPUT}
            ]
        }

# Create and inject the mock llama_cpp module
mock_llama_cpp = types.ModuleType('llama_cpp')
setattr(mock_llama_cpp, 'Llama', MockLlama)
sys.modules['llama_cpp'] = mock_llama_cpp

# Import core with mocked os.listdir to ensure a model file is found
with patch('os.listdir', return_value=['model.gguf']):
    import core

# Override DISPLAY_EXTENDED_REASONING for all tests
core.DISPLAY_EXTENDED_REASONING = True

# Test inputs
PRIME_DIRECTIVES = "You are a friendly AI assistant."
PROMPT = "Hello, how are you?"
PREVIOUS_PRIME_DIRECTIVES = "Previous prime directives"
PREVIOUS_PROMPT = "Previous prompt"
BINARY_QUESTION = "Is this a test?"

# Test responses
BASIC_RESPONSE = "I'm a helpful assistant."
# The raw continuation the mock model returns (no opening <think>, that comes from THINK_TRIGGER)
MOCK_MODEL_OUTPUT = "This is a thought.\n</think>\n" + BASIC_RESPONSE
# What send_prompt actually returns with DISPLAY_EXTENDED_REASONING=True
NORMAL_RESPONSE = core.THINK_TRIGGER + MOCK_MODEL_OUTPUT
REPEATED_THINK_END_TAG_RESPONSE = (
    "<think>\n"
    "Reasoning.\n"
    "</think>\n\n"
    "Old answer.\n"
    "</think>\n\n"
    "Final answer."
)
REPEATED_THINK_END_TAG_FINAL_RESPONSE = "Final answer."
PREVIOUS_RESPONSE = "Previous response"
YES_RESPONSE = "Yes"
MULTILINE_YES_RESPONSE = "Reasoning here\nYes"
MALFORMED_YES_RESPONSE = "\"'Yes."
NO_RESPONSE = "No"


class TestCore(unittest.TestCase):

    def setUp(self):
        # Set up model instance for testing
        core.model = MockLlama(model_path="model.gguf", n_ctx=core.CONTEXT_SIZE)

    def test_empty_context(self):
        """Test send_prompt with empty context - should add prime directives"""
        # Setup
        context = []

        # Execute
        response = core.send_prompt(PRIME_DIRECTIVES, PROMPT, context)

        # Check response
        self.assertEqual(response, NORMAL_RESPONSE)

        # Check context size
        self.assertEqual(len(context), 3)

        # Check first element contains system + prime directives
        self.assertEqual(
            context[0],
            core.SYSTEM_TEXT + PRIME_DIRECTIVES + core.EOS
        )

        # Check second element has user prompt + EOS + assistant tag
        self.assertEqual(
            context[1],
            core.USER_TEXT + PROMPT + core.EOS + core.ASSISTANT_TEXT
        )

        # Check third element stores only the final answer + EOS
        self.assertEqual(context[2], BASIC_RESPONSE + core.EOS)

    def test_existing_context(self):
        """Test send_prompt with existing context - should overwrite prime directives"""
        # Context already has some messages
        context = [
            core.SYSTEM_TEXT + PREVIOUS_PRIME_DIRECTIVES + core.EOS,
            core.USER_TEXT + PREVIOUS_PROMPT + core.EOS + core.ASSISTANT_TEXT,
            PREVIOUS_RESPONSE + core.EOS
        ]

        # Execute
        response = core.send_prompt(PRIME_DIRECTIVES, PROMPT, context)

        # Check response
        self.assertEqual(response, NORMAL_RESPONSE)

        # Check context size
        self.assertEqual(len(context), 5)

        # First element should contain the new prime directives
        self.assertEqual(
            context[0],
            core.SYSTEM_TEXT + PRIME_DIRECTIVES + core.EOS
        )

        # New user prompt should be appended
        self.assertEqual(
            context[3],
            core.USER_TEXT + PROMPT + core.EOS + core.ASSISTANT_TEXT
        )

        # New response should be appended with historical reasoning removed
        self.assertEqual(context[4], BASIC_RESPONSE + core.EOS)

    def test_hide_reasoning_true(self):
        """Test send_prompt with hide_reasoning explicitly set to True"""
        # Setup
        context = []

        # Execute - reasoning should be removed
        response = core.send_prompt(PRIME_DIRECTIVES, PROMPT, context, hide_reasoning=True)

        # Assert - the response should have thinking tags removed
        self.assertEqual(response, BASIC_RESPONSE)

        # Check context contains only the final response + EOS
        self.assertEqual(context[2], BASIC_RESPONSE + core.EOS)

    def test_hide_reasoning_positional(self):
        """Test fourth positional argument remains hide_reasoning"""
        context = []

        response = core.send_prompt(PRIME_DIRECTIVES, PROMPT, context, True)

        self.assertEqual(response, BASIC_RESPONSE)
        self.assertTrue(core.model.last_prompt.endswith(core.ASSISTANT_TEXT + core.THINK_TRIGGER))
        self.assertEqual(core.model.last_call_kwargs['temperature'], core.TEMPERATURE_THINKING)
        self.assertEqual(core.model.last_call_kwargs['top_p'], core.TOP_P_THINKING)

    def test_remove_reasoning_repeated_think_end_tag(self):
        """Test repeated THINK_END tags keep only the regenerated final answer"""
        self.assertEqual(
            core.remove_reasoning(REPEATED_THINK_END_TAG_RESPONSE),
            REPEATED_THINK_END_TAG_FINAL_RESPONSE
        )

    def test_get_completion_thinking(self):
        """Test thinking mode uses open think block and thinking sampling"""
        context = [
            core.SYSTEM_TEXT + PRIME_DIRECTIVES + core.EOS,
            core.USER_TEXT + PROMPT + core.EOS + core.ASSISTANT_TEXT
        ]

        response = core.get_completion_from_messages(context, thinking=True)

        self.assertEqual(response, NORMAL_RESPONSE)
        self.assertTrue(core.model.last_prompt.endswith(core.ASSISTANT_TEXT + core.THINK_TRIGGER))
        self.assertEqual(core.model.last_call_kwargs['temperature'], core.TEMPERATURE_THINKING)
        self.assertEqual(core.model.last_call_kwargs['top_p'], core.TOP_P_THINKING)
        self.assertEqual(
            context[-1],
            core.USER_TEXT + PROMPT + core.EOS + core.ASSISTANT_TEXT
        )

    def test_get_completion_non_thinking(self):
        """Test non-thinking mode uses closed think block and instruct sampling"""
        context = [
            core.SYSTEM_TEXT + PRIME_DIRECTIVES + core.EOS,
            core.USER_TEXT + PROMPT + core.EOS + core.ASSISTANT_TEXT
        ]

        with patch(__name__ + '.MOCK_MODEL_OUTPUT', BASIC_RESPONSE):
            response = core.get_completion_from_messages(context, thinking=False)

        expected_suffix = core.ASSISTANT_TEXT + core.THINK_TRIGGER + core.THINK_CLOSER

        self.assertEqual(response, BASIC_RESPONSE)
        self.assertTrue(core.model.last_prompt.endswith(expected_suffix))
        self.assertEqual(core.model.last_call_kwargs['temperature'], core.TEMPERATURE_INSTRUCT)
        self.assertEqual(core.model.last_call_kwargs['top_p'], core.TOP_P_INSTRUCT)
        self.assertEqual(
            context[-1],
            core.USER_TEXT + PROMPT + core.EOS + core.ASSISTANT_TEXT
        )

    def test_send_prompt_non_thinking(self):
        """Test send_prompt stores and returns a direct non-thinking response"""
        context = []

        with patch(__name__ + '.MOCK_MODEL_OUTPUT', BASIC_RESPONSE):
            response = core.send_prompt(
                PRIME_DIRECTIVES,
                PROMPT,
                context,
                thinking=False,
                hide_reasoning=True
            )

        expected_command = core.USER_TEXT + PROMPT + core.EOS + core.ASSISTANT_TEXT
        expected_inference_suffix = core.ASSISTANT_TEXT + core.THINK_TRIGGER + core.THINK_CLOSER

        self.assertEqual(response, BASIC_RESPONSE)
        self.assertTrue(core.model.last_prompt.endswith(expected_inference_suffix))
        self.assertEqual(context[1], expected_command)
        self.assertEqual(context[2], BASIC_RESPONSE + core.EOS)

    def test_empty_response(self):
        """Test send_prompt when get_completion_from_messages returns an empty string"""
        # Setup
        context = []

        # Execute
        with patch.object(core, 'get_completion_from_messages', return_value=""):
            response = core.send_prompt(PRIME_DIRECTIVES, PROMPT, context)

        # Assert
        self.assertEqual(response, "")
        self.assertEqual(len(context), 3)

        # Check third element only has EOS
        self.assertEqual(context[2], core.EOS)

    def test_empty_prime_directives(self):
        """Test send_prompt with empty prime_directives"""
        # Setup
        context = []

        # Execute
        response = core.send_prompt("", PROMPT, context)

        # Assert - by default, reasoning should be preserved
        self.assertEqual(response, NORMAL_RESPONSE)

        # Check first element contains just system + EOS
        self.assertEqual(context[0], core.SYSTEM_TEXT + core.EOS)

        # Check context stores only the final answer.
        self.assertEqual(context[2], BASIC_RESPONSE + core.EOS)


    def test_empty_prompt(self):
        """Test send_prompt with empty prompt"""
        # Setup
        context = []

        # Execute
        response = core.send_prompt(PRIME_DIRECTIVES, "", context)

        # Assert - by default, reasoning should be preserved
        self.assertEqual(response, NORMAL_RESPONSE)

        # Check second element has empty user prompt + EOS + assistant tag
        self.assertEqual(context[1], core.USER_TEXT + core.EOS + core.ASSISTANT_TEXT)

        # Check context stores only the final answer.
        self.assertEqual(context[2], BASIC_RESPONSE + core.EOS)


    def test_context_trimming(self):
        """Test that context is properly trimmed when token count exceeds MAX_INPUT_TOKENS"""

        # Set response size to guarantee we exceed MAX_INPUT_TOKENS
        response_size = (core.MAX_INPUT_TOKENS * 2) // 3

        # Start with a context that already has two exchanges with large responses
        context = [
            core.SYSTEM_TEXT + PRIME_DIRECTIVES + core.EOS,                     # Position 0: System
            core.USER_TEXT + "First message" + core.EOS + core.ASSISTANT_TEXT,  # Position 1: User 1
            "X" * response_size + core.EOS,                                     # Position 2: Response 1
            core.USER_TEXT + "Second message" + core.EOS + core.ASSISTANT_TEXT, # Position 3: User 2
            "Y" * response_size + core.EOS                                      # Position 4: Response 2
        ]

        # Save original context
        original_context = context.copy()

        # Add another message via send_prompt, which should trigger trimming
        third_message = "Third message"
        response = core.send_prompt(PRIME_DIRECTIVES, third_message, context)

        # Check response
        self.assertEqual(response, NORMAL_RESPONSE)

        # After send_prompt, we should have:
        # - System message (preserved)
        # - The second exchange (positions 3-4 from original) moved to positions 1-2
        # - The new exchange (third message + response) at positions 3-4
        # Total: 5 elements

        # Check expected length
        self.assertEqual(len(context), 5)

        # Check contents
        self.assertEqual(context[0], original_context[0])  # System message preserved
        self.assertEqual(context[1], original_context[3])  # Second user message
        self.assertEqual(context[2], original_context[4])  # Second response
        self.assertEqual(context[3], core.USER_TEXT + third_message + core.EOS + core.ASSISTANT_TEXT)

        # Check the final context element stores only the final answer
        self.assertEqual(context[4], BASIC_RESPONSE + core.EOS)


    def test_minimum_context_reserves_two_responses(self):
        """The configured minimum must reserve at least two response-sized windows."""
        self.assertGreaterEqual(core.MIN_CONTEXT_SIZE, 2 * core.MAX_RESPONSE_SIZE)
        self.assertGreaterEqual(core.CONTEXT_SIZE, core.MIN_CONTEXT_SIZE)
        self.assertEqual(core.MAX_INPUT_TOKENS, core.CONTEXT_SIZE - core.MAX_RESPONSE_SIZE - core.CONTEXT_HEADROOM)

    def test_previous_exchange_preserved_when_over_input_budget(self):
        """Do not discard the only previous exchange even when it exceeds the preferred input budget."""
        previous_user = core.USER_TEXT + "Previous request" + core.EOS + core.ASSISTANT_TEXT
        previous_assistant = "P" * core.MAX_INPUT_TOKENS + core.EOS
        context = [
            core.SYSTEM_TEXT + PRIME_DIRECTIVES + core.EOS,
            previous_user,
            previous_assistant,
        ]

        response = core.send_prompt(PRIME_DIRECTIVES, "Follow-up request", context)

        self.assertEqual(response, NORMAL_RESPONSE)
        self.assertEqual(len(context), 5)
        self.assertEqual(context[1:3], [previous_user, previous_assistant])
        self.assertGreater(core.get_number_of_tokens(core.model.last_prompt), core.MAX_INPUT_TOKENS)
        self.assertGreaterEqual(core.model.last_call_kwargs['max_tokens'], core.MIN_RESPONSE_SIZE)

    def test_trim_older_but_protect_last_exchange_over_budget(self):
        """Trim older turns without continuing into the protected immediately previous turn."""
        oldest_user = core.USER_TEXT + "Oldest request" + core.EOS + core.ASSISTANT_TEXT
        previous_user = core.USER_TEXT + "Previous request" + core.EOS + core.ASSISTANT_TEXT
        previous_assistant = "P" * core.MAX_INPUT_TOKENS + core.EOS
        context = [
            core.SYSTEM_TEXT + PRIME_DIRECTIVES + core.EOS,
            oldest_user,
            "O" * (core.MAX_INPUT_TOKENS // 3) + core.EOS,
            previous_user,
            previous_assistant,
        ]

        response = core.send_prompt(PRIME_DIRECTIVES, "Follow-up request", context)

        self.assertEqual(response, NORMAL_RESPONSE)
        self.assertEqual(len(context), 5)
        self.assertEqual(context[1:3], [previous_user, previous_assistant])
        self.assertNotIn(oldest_user, context)
        self.assertGreater(core.get_number_of_tokens(core.model.last_prompt), core.MAX_INPUT_TOKENS)


    def test_multiple_turns_do_not_store_reasoning(self):
        """Previous thinking must not reappear in a subsequent inference prompt."""
        context = []
        first = core.send_prompt(PRIME_DIRECTIVES, "First question", context)
        self.assertEqual(first, NORMAL_RESPONSE)
        self.assertEqual(context[2], BASIC_RESPONSE + core.EOS)

        with patch(__name__ + '.MOCK_MODEL_OUTPUT', "Second thought.\n</think>\nSecond answer"):
            second = core.send_prompt(PRIME_DIRECTIVES, "Second question", context)

        self.assertIn("Second answer", second)
        self.assertNotIn("This is a thought.", core.model.last_prompt)
        self.assertEqual(context[2], BASIC_RESPONSE + core.EOS)
        self.assertEqual(context[4], "Second answer" + core.EOS)

    def test_non_thinking_without_hide_reasoning_stores_plain_answer(self):
        """Instruct-mode history stays clean even with display enabled."""
        context = []
        with patch(__name__ + '.MOCK_MODEL_OUTPUT', BASIC_RESPONSE):
            result = core.send_prompt(PRIME_DIRECTIVES, PROMPT, context, thinking=False)
        self.assertEqual(result, BASIC_RESPONSE)
        self.assertEqual(context[2], BASIC_RESPONSE + core.EOS)
        self.assertFalse(context[1].endswith(core.THINK_CLOSER))
        self.assertNotIn(core.THINK_TRIGGER, ''.join(context))

    def test_display_flag_does_not_change_stored_history(self):
        """DISPLAY_EXTENDED_REASONING changes presentation, never saved context."""
        context = []
        with patch.object(core, 'DISPLAY_EXTENDED_REASONING', False):
            result = core.send_prompt(PRIME_DIRECTIVES, PROMPT, context)
        self.assertEqual(result, BASIC_RESPONSE)
        self.assertEqual(context[2], BASIC_RESPONSE + core.EOS)

    def test_oversized_prompt_cleans_temporary_tags_thinking(self):
        """Oversized responses return an error without modifying the command."""
        context = [
            core.SYSTEM_TEXT + PRIME_DIRECTIVES + core.EOS,
            core.USER_TEXT + PROMPT + core.EOS + core.ASSISTANT_TEXT,
        ]
        before = context[-1]
        with patch.object(core, 'MIN_RESPONSE_SIZE', core.CONTEXT_SIZE + 1):
            result = core.get_completion_from_messages(context, thinking=True)
        self.assertEqual(result, core.OVERSIZED_PROMPT_ERROR)
        self.assertEqual(context[-1], before)

    def test_oversized_prompt_cleans_temporary_tags_instruct(self):
        """Oversized instruct-mode prompts do not leave empty thinking blocks."""
        context = [
            core.SYSTEM_TEXT + PRIME_DIRECTIVES + core.EOS,
            core.USER_TEXT + PROMPT + core.EOS + core.ASSISTANT_TEXT,
        ]
        before = context[-1]
        with patch.object(core, 'MIN_RESPONSE_SIZE', core.CONTEXT_SIZE + 1):
            result = core.get_completion_from_messages(context, thinking=False)
        self.assertEqual(result, core.OVERSIZED_PROMPT_ERROR)
        self.assertEqual(context[-1], before)

    def test_instruct_mode_response_with_literal_inline_think_tag(self):
        """Strict newline-based parser preserves conversational inline markers."""
        raw = 'The user wrote <think> as text, not a reasoning block.'
        context = []
        with patch(__name__ + '.MOCK_MODEL_OUTPUT', raw):
            result = core.send_prompt(PRIME_DIRECTIVES, PROMPT, context, thinking=False)
        self.assertEqual(result, raw)
        self.assertEqual(context[2], raw + core.EOS)

    def test_inference_error_terminates(self):
        """A model exception terminates, so context cleanup is unnecessary."""
        context = [
            core.SYSTEM_TEXT + PRIME_DIRECTIVES + core.EOS,
            core.USER_TEXT + PROMPT + core.EOS + core.ASSISTANT_TEXT,
        ]
        with patch.object(MockLlama, '__call__', side_effect=RuntimeError('fail')):
            with self.assertRaises(SystemExit):
                core.get_completion_from_messages(context, thinking=False)



class TestSummary(unittest.TestCase):
    def setUp(self):
        # Set up model instance for testing
        core.model = MockLlama(model_path="model.gguf", n_ctx=core.CONTEXT_SIZE)

        # Save original values to restore after tests
        self.original_block_words = core.TEXT_BLOCK_WORDS

    def tearDown(self):
        # Restore original values after tests
        core.TEXT_BLOCK_WORDS = self.original_block_words

    def test_split_text_in_blocks(self):
        """Test split_text_in_blocks function with various text inputs"""
        # Temporarily set to small value for testing
        core.TEXT_BLOCK_WORDS = 3

        # Case 1: Empty text - should return empty array
        result = core.split_text_in_blocks("")
        self.assertEqual(result, [])

        # Case 2: Text with fewer words than block size
        result = core.split_text_in_blocks("Word1 Word2")
        self.assertEqual(result, ["Word1 Word2"])

        # Case 3: Text with exactly one block
        result = core.split_text_in_blocks("Word1 Word2 Word3")
        self.assertEqual(result, ["Word1 Word2 Word3"])

        # Case 4: Text with multiple blocks
        result = core.split_text_in_blocks("Word1 Word2 Word3 Word4 Word5 Word6 Word7")
        self.assertEqual(result, ["Word1 Word2 Word3", "Word4 Word5 Word6", "Word7"])

    def test_summarize_uses_non_thinking(self):
        """Test summarize explicitly disables reasoning"""
        topic = "Test topic"
        text = "Test data"

        with patch.object(core, 'send_prompt', return_value="Summary") as mock_send:
            result = core.summarize(topic, text)

        mock_send.assert_called_once_with(
            core.SUMMARIZE_SYSTEM_PROMPT,
            core.DATA_ONLY_START_TAG + text + core.DATA_ONLY_END_TAG + core.SUMMARIZE_TEXT + topic,
            [],
            thinking=False,
            hide_reasoning=True
        )
        self.assertEqual(result, "Summary")

    def test_update_summary(self):
        """Test update_summary function with various combinations of inputs"""
        topic = "Test topic"

        # Case 1: Empty text, existing summary - should return summary unchanged
        result = core.update_summary(topic, "Existing summary", "")
        self.assertEqual(result, "Existing summary")

        # Case 2: Empty summary, non-empty text - should return text directly
        result = core.update_summary(topic, "", "New text")
        self.assertEqual(result, "New text")

        # Case 3: Both summary and text exist - should summarize combined text
        with patch.object(core, 'summarize', return_value="Updated summary") as mock_summarize:
            result = core.update_summary(topic, "Existing summary", "New text")
            mock_summarize.assert_called_once_with(topic, "PREVIOUS_SUMMARY:\nExisting summary\n\nNEW_TEXT:\nNew text")
            self.assertEqual(result, "Updated summary")

    def test_summarize_block_array(self):
        """Test summarize_block_array with various block arrays"""
        topic = "Test topic"

        # Case 1: Empty block array - should return empty string
        result = core.summarize_block_array(topic, [])
        self.assertEqual(result, "")

        # Case 2: Single block - should return block directly (via update_summary)
        with patch.object(core, 'summarize') as mock_summarize:
            result = core.summarize_block_array(topic, ["Block 1"])
            # The update_summary function should not call summarize for a single block with empty initial summary
            mock_summarize.assert_not_called()
            self.assertEqual(result, "Block 1")

        # Case 3: Multiple blocks - should call summarize to combine blocks
        with patch.object(core, 'summarize', return_value="Combined summary") as mock_summarize:
            result = core.summarize_block_array(topic, ["Block 1", "Block 2", "Block 3"])

            # Check that summarize was called
            mock_summarize.assert_called()
            self.assertEqual(result, "Combined summary")

    def test_load_mission_data(self):
        """Test load_mission_data with various mission data scenarios"""
        prompt = "Test topic"

        # Case 1: Empty mission data - should return empty string
        with patch.object(core, 'read_text_file', return_value=""):
            result = core.load_mission_data(prompt)
            self.assertEqual(result, "")

        # Case 2: Short mission data - should return data without summarization
        short_data = "Short mission data"
        with patch.object(core, 'read_text_file', return_value=short_data):
            result = core.load_mission_data(prompt)
            self.assertEqual(result, short_data)

        # Case 3: Long mission data - should split and summarize
        # Create a string longer than TEXT_BLOCK_WORDS
        long_data = " ".join(["word"] * (core.TEXT_BLOCK_WORDS + 100))
        expected_summary = "Summarized mission data"

        with patch.object(core, 'read_text_file', return_value=long_data):
            with patch.object(core, 'summarize', return_value=expected_summary):
                result = core.load_mission_data(prompt)
                self.assertEqual(result, expected_summary)


class TestBinaryQuestion(unittest.TestCase):
    def setUp(self):
        # Set up model instance for testing
        core.model = MockLlama(model_path="model.gguf", n_ctx=core.CONTEXT_SIZE)

    def test_yes_response(self):
        """Test binary_question with a 'Yes' response"""
        context = []

        with patch.object(core, 'send_prompt', return_value = YES_RESPONSE) as mock_send:
            result = core.binary_question(PRIME_DIRECTIVES, BINARY_QUESTION, context)
            mock_send.assert_called_once()
            self.assertTrue(result)

    def test_no_response(self):
        """Test binary_question with a 'No' response"""
        context = []

        with patch.object(core, 'send_prompt', return_value = NO_RESPONSE) as mock_send:
            result = core.binary_question(PRIME_DIRECTIVES, BINARY_QUESTION, context)
            mock_send.assert_called_once()
            self.assertFalse(result)

    def test_multi_line_yes(self):
        """Test binary_question with multi-line response ending in 'yes'"""
        context = []

        with patch.object(core, 'send_prompt', return_value = MULTILINE_YES_RESPONSE) as mock_send:
            result = core.binary_question(PRIME_DIRECTIVES, BINARY_QUESTION, context)
            mock_send.assert_called_once()
            self.assertTrue(result)

    def test_malformed_yes(self):
        """Test binary_question with malformed 'yes'"""
        context = []

        with patch.object(core, 'send_prompt', return_value = MALFORMED_YES_RESPONSE) as mock_send:
            result = core.binary_question(PRIME_DIRECTIVES, BINARY_QUESTION, context)
            mock_send.assert_called_once()
            self.assertTrue(result)

    def test_yes_substring_response(self):
        """Test responses merely containing YES are not accepted"""
        context = []

        with patch.object(core, 'send_prompt', return_value="Yesterday"):
            self.assertFalse(core.binary_question(PRIME_DIRECTIVES, BINARY_QUESTION, context))

        with patch.object(core, 'send_prompt', return_value="No, not yes"):
            self.assertFalse(core.binary_question(PRIME_DIRECTIVES, BINARY_QUESTION, context))

    def test_empty_response(self):
        """Test binary_question with empty response"""
        context = []

        with patch.object(core, 'send_prompt', return_value="") as mock_send:
            result = core.binary_question(PRIME_DIRECTIVES, BINARY_QUESTION, context)
            mock_send.assert_called_once()
            self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
