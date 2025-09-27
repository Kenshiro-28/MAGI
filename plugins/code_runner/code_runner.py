# ruff: noqa: S603
import subprocess
import os
import sys

PROGRAM_TIMEOUT = 1800
CODE_RUNNER_ERROR = "\n[ERROR] Code Runner error: "
RUFF_IGNORED_RULES = "D,E501,F541,I,N,PT,W,S105,S106"

def run_python_code(program: str):
    try:
        package_list = []

        # Get the Python package_list to install
        for line in program.splitlines():
            line = line.strip()

            if line.startswith('# pip install '):
                package_list.extend(line[13:].split())

        # Install Python packages
        if package_list:
            result = subprocess.run([PIP_EXEC_PATH, 'install', '--upgrade'] + package_list, capture_output = True, text = True)

            if result.returncode != 0:
                pip_output = result.stdout + "\n" + result.stderr
                return pip_output, ""

        # Lint with ruff using stdin
        lint_output_data = subprocess.run(
            [RUFF_EXEC_PATH, 'check', '-', '--stdin-filename=program.py', '--ignore', RUFF_IGNORED_RULES],
            input = program,
            capture_output = True,
            text = True
        )

        lint_output = lint_output_data.stdout + lint_output_data.stderr

        # If there is a lint error, return only the lint output
        if lint_output_data.returncode != 0:
            return lint_output, ""

        # Execute program using -c
        program_output_data = subprocess.run([PYTHON_EXEC_PATH, '-c', program], capture_output = True, text = True, timeout = PROGRAM_TIMEOUT)
        program_output = program_output_data.stdout.strip()

        # Append error data to program output
        if program_output_data.returncode != 0:
            program_output += "\n\nError: " + program_output_data.stderr
            program_output += "\nReturn code: " + str(program_output_data.returncode)

        return lint_output, program_output

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


