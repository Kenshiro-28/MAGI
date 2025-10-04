# ruff: noqa: S603
import subprocess
import os
import sys

PROGRAM_TIMEOUT = 1800
CODE_RUNNER_ERROR = "\n[ERROR] Code Runner error: "
RUFF_IGNORED_RULES = "D,E501,F541,I,N,PT,W,S105,S106"
LINT_OUTPUT_TEXT = "----- LINT OUTPUT -----\n\n"
PACKAGE_INSTALLATION_TEXT = "----- PACKAGE INSTALLATION -----\n\npip install "
PROGRAM_OUTPUT_TEXT = "\n----- PROGRAM OUTPUT -----\n\n"
PROGRAM_ERROR_TEXT = "\n\nProgram error: "
PROGRAM_RETURN_CODE_TEXT = "\nReturn code: "
PACKAGE_LIST_COMMENT = "# pip install "


def run_python_code(program: str):
    try:
        package_list = []
        pip_output = ""

        # Get the Python package_list to install
        for line in program.splitlines():
            line = line.strip()

            if line.startswith(PACKAGE_LIST_COMMENT):
                package_list.extend(line[len(PACKAGE_LIST_COMMENT):].strip().split())

        # Install Python packages
        if package_list:
            result = subprocess.run([PIP_EXEC_PATH, 'install', '--upgrade'] + package_list, capture_output = True, text = True)

            pip_output = PACKAGE_INSTALLATION_TEXT + ' '.join(package_list) + "\n\n" + result.stdout

            # Append error output
            if result.stderr:
                pip_output += "\n\n" + result.stderr

            # If there is an error, return only the pip install output
            if result.returncode != 0:
                return pip_output.strip(), ""

        # Lint with ruff using stdin
        lint_output_data = subprocess.run(
            [RUFF_EXEC_PATH, 'check', '-', '--stdin-filename=program.py', '--ignore', RUFF_IGNORED_RULES, '--verbose'],
            input = program,
            capture_output = True,
            text = True
        )

        lint_output = LINT_OUTPUT_TEXT + lint_output_data.stdout + "\n" + lint_output_data.stderr

        # If there is a lint error, return only the lint output
        if lint_output_data.returncode != 0:
            return lint_output.strip(), ""

        # Execute program
        program_output_data = subprocess.run([PYTHON_EXEC_PATH, '-c', program], capture_output = True, text = True, timeout = PROGRAM_TIMEOUT)
        program_output = PROGRAM_OUTPUT_TEXT + program_output_data.stdout.strip()

        # Append error data to program output
        if program_output_data.returncode != 0:
            program_output += PROGRAM_ERROR_TEXT + program_output_data.stderr
            program_output += PROGRAM_RETURN_CODE_TEXT + str(program_output_data.returncode)

        # Prepend pip install output
        program_output = pip_output + program_output

        return lint_output.strip(), program_output.strip()

    except Exception as e:
        print(CODE_RUNNER_ERROR + str(e))
        return "", ""


# INITIALIZE

try:
    current_path = os.getcwd()

    # Get path of Python virtual environment
    venv_path = os.path.join(current_path, 'venv')

    # Create Python virtual environment
    if not os.path.exists(venv_path):
        subprocess.check_call([sys.executable, '-m', 'venv', venv_path])

    # Get Python, Pip and Ruff executable paths
    PYTHON_EXEC_PATH = os.path.join(venv_path, 'bin', 'python')
    PIP_EXEC_PATH = os.path.join(venv_path, 'bin', 'pip')
    RUFF_EXEC_PATH = os.path.join(venv_path, 'bin', 'ruff')

    # Install/upgrade Ruff
    subprocess.check_call([PIP_EXEC_PATH, 'install', '--upgrade', '--quiet', 'ruff'])

except Exception as e:
    print(CODE_RUNNER_ERROR + str(e))
    raise


