# ruff: noqa: S603
import subprocess
import os
import sys
import stat
import shutil

PROGRAM_TIMEOUT = 1800
CODE_RUNNER_ERROR = "\n[ERROR] Code Runner error: "
RUFF_IGNORED_RULES = "D,E501,F401,F541,I,N,PT,W,S105,S106"
LINT_OUTPUT_TEXT = "----- LINT OUTPUT -----\n\n"
PACKAGE_INSTALLATION_TEXT = "----- PACKAGE INSTALLATION -----\n\npip install "
PROGRAM_OUTPUT_TEXT = "\n----- PROGRAM OUTPUT -----\n\n"
PROGRAM_ERROR_TEXT = "\n\nProgram error: "
PROGRAM_RETURN_CODE_TEXT = "\nReturn code: "
PACKAGE_LIST_COMMENT = "# pip install "


def _install_packages(package_list):
    result = subprocess.run([PIP_EXEC_PATH, 'install', '--upgrade'] + package_list, capture_output = True, text = True)

    return result


def _remove_readonly(func, path, exc_info):
    if func in (os.unlink, os.rmdir):
        os.chmod(path, stat.S_IWRITE)
        func(path)


def _create_venv():
    # Delete previous environment and cache
    shutil.rmtree(VENV_PATH, onerror = _remove_readonly)
    shutil.rmtree(PYCACHE_PATH, onerror = _remove_readonly)

    # Create new environment
    subprocess.check_call([sys.executable, '-m', 'venv', VENV_PATH])

    # Install Ruff
    subprocess.check_call([PIP_EXEC_PATH, 'install', '--quiet', 'ruff'])


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
            result = _install_packages(package_list)

            # If failed, recreate venv and try again
            if result.returncode != 0:
                _create_venv()
                result = _install_packages(package_list)

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
        program_output_data = subprocess.run(
            [PYTHON_EXEC_PATH, '-c', program],
            capture_output = True,
            text = True,
            timeout = PROGRAM_TIMEOUT,
            cwd = WORKSPACE_PATH
        )
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
    CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))

    # Get path of MAGI root folder
    ROOT_PATH = os.path.dirname(os.path.dirname(CURRENT_PATH))

    # Get path of workspace folder
    WORKSPACE_PATH = os.path.join(ROOT_PATH, 'workspace')
    os.makedirs(WORKSPACE_PATH, exist_ok = True)

    # Get path of Python virtual environment
    VENV_PATH = os.path.join(CURRENT_PATH, 'venv')

    # Get path of Python cache
    PYCACHE_PATH = os.path.join(CURRENT_PATH, '__pycache__')

    # Get Python, Pip and Ruff executable paths
    PYTHON_EXEC_PATH = os.path.join(VENV_PATH, 'bin', 'python')
    PIP_EXEC_PATH = os.path.join(VENV_PATH, 'bin', 'pip')
    RUFF_EXEC_PATH = os.path.join(VENV_PATH, 'bin', 'ruff')

    # Check Python virtual environment
    if os.path.exists(VENV_PATH) and os.path.exists(PIP_EXEC_PATH):
        # Upgrade Ruff
        subprocess.check_call([PIP_EXEC_PATH, 'install', '--upgrade', '--quiet', 'ruff'])
    else:
        # Create new Python virtual environment
        _create_venv()

except Exception as e:
    print(CODE_RUNNER_ERROR + str(e))
    raise


