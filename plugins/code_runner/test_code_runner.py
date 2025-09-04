import code_runner

SAMPLE_CODE_GOOD = 'print("Hello, MAGI!")'

SAMPLE_CODE_LINT_ERROR = 'import os\nprint(1)'

SAMPLE_CODE_RUNTIME_ERROR = 'print(1/0)'

SAMPLE_CODE_PACKAGE = '# pip install numpy requests\nimport numpy as np\nprint(np.array([1,2,3]))'


def _print_result(lint_output, program_output):
    print("\nLint: " + lint_output)
    print("Output: " + program_output)


# Good code test
print("\n----- Running good code -----\n\n" + SAMPLE_CODE_GOOD + "\n")

lint_output, program_output = code_runner.run_python_code(SAMPLE_CODE_GOOD)
_print_result(lint_output, program_output)

# Lint issue test (unused import)
print("\n----- Running code with lint issue -----\n\n" + SAMPLE_CODE_LINT_ERROR + "\n")

lint_output, program_output = code_runner.run_python_code(SAMPLE_CODE_LINT_ERROR)
_print_result(lint_output, program_output)

# Runtime error test
print("\n----- Running code with runtime error -----\n\n" + SAMPLE_CODE_RUNTIME_ERROR + "\n")

lint_output, program_output = code_runner.run_python_code(SAMPLE_CODE_RUNTIME_ERROR)
_print_result(lint_output, program_output)

# Package install test
print("\n----- Running code with package install -----\n\n" + SAMPLE_CODE_PACKAGE + "\n")

lint_output, program_output = code_runner.run_python_code(SAMPLE_CODE_PACKAGE)
_print_result(lint_output, program_output)


