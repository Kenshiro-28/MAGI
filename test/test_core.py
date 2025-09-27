import unittest
import sys
from unittest.mock import patch

# Create a mock for the Llama class that will be imported in core.py
class MockLlama:
    def __init__(self, model_path=None, n_ctx=None, **kwargs):
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.verbose = True
        self.kwargs = kwargs

    def tokenize(self, text):
        # Simple mock tokenizer that counts characters as tokens
        return [ord(c) for c in text.decode('utf-8')]

    def __call__(self, prompt, max_tokens=100, temperature=1.0, **kwargs):
        return {
            'choices': [
                {'text': NORMAL_RESPONSE}
            ]
        }

# Create and inject the mock llama_cpp module
sys.modules['llama_cpp'] = type('llama_cpp', (), {'Llama': MockLlama})

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
NORMAL_RESPONSE = "<think>This is a thought.</think>" + BASIC_RESPONSE
BASIC_MULTIPLE_THINKING_RESPONSE = "Hello there!"
MULTIPLE_THINKING_RESPONSE = "<think>First thought.</think>\nHello<think>\nAnother thought.\n</think>\n there!"
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

        # Check third element has the basic response + EOS
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

        # New response should be appended (without extended reasoning)
        self.assertEqual(context[4], BASIC_RESPONSE + core.EOS)

    def test_hide_reasoning_true(self):
        """Test send_prompt with hide_reasoning explicitly set to True"""
        # Setup
        context = []

        # Execute - reasoning should be removed
        response = core.send_prompt(PRIME_DIRECTIVES, PROMPT, context, hide_reasoning=True)

        # Assert - the response should have thinking tags removed
        self.assertEqual(response, BASIC_RESPONSE)

        # Check context contains the basic response + EOS
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

        # Check context response doesn't contain extended reasoning.
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

        # Check context response doesn't contain extended reasoning.
        self.assertEqual(context[2], BASIC_RESPONSE + core.EOS)

    def test_multiple_thinking_blocks(self):
        """Test send_prompt with multiple thinking blocks"""
        # Setup
        context = []

        # Execute (get_completion_from_messages shouldn't return the first <think> tag)
        with patch.object(core, 'get_completion_from_messages', return_value=MULTIPLE_THINKING_RESPONSE):
            response = core.send_prompt(PRIME_DIRECTIVES, PROMPT, context, hide_reasoning=True)

        # Assert - all thinking tags should be removed
        self.assertEqual(response, BASIC_MULTIPLE_THINKING_RESPONSE)

        # Check context contains the basic response + EOS
        self.assertEqual(context[2], BASIC_MULTIPLE_THINKING_RESPONSE + core.EOS)

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

        # Check the final context element stores the basic response
        self.assertEqual(context[4], BASIC_RESPONSE + core.EOS)


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
            mock_summarize.assert_called_once_with(topic, "Existing summary\nNew text")
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

    def test_empty_response(self):
        """Test binary_question with empty response"""
        context = []

        with patch.object(core, 'send_prompt', return_value="") as mock_send:
            result = core.binary_question(PRIME_DIRECTIVES, BINARY_QUESTION, context)
            mock_send.assert_called_once()
            self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
