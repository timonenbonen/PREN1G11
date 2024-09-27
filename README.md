# PREN1 Gruppe 11

This repository contains the code for the PREN1 project.

This README is a work in progress and will be updated as the project progresses.

## Installation

### Windows

For windows, you can use the following commands after [installing Python 3.11](https://www.python.org/downloads/) or higher:

```bash
python -m pip install pipx --user
python -m pipx install poetry
python -m pipx ensurepath

# Restart the terminal

poetry install
```

There may be issues installing certain dependencies on Windows, remove the dependencies from the `pyproject.toml` file temporarily and run `poetry install` again. Remember to mock the dependencies using `.env` if necessary.

### Raspberry Pi

**First setup only:** To clone the repository on the Raspberry Pi, you need to create a new ssh key and add it to the GitHub repository.

- Create a new ssh key on your Raspberry Pi with the following command: `ssh-keygen -t ed25519 -C "<name>@stud.hslu.ch"`
- Copy the public key: `cat ~/.ssh/id_ed25519.pub`
- Add the public key to the GitHub repository under [`Settings > Deploy keys`](https://github.com/timonenbonen/PREN1G11/settings/keys) (only the repository owner can do this)

```bash
git clone git@github.com:timonenbonen/PREN1G11.git
```

Then you can run the following script inside the cloned folder to install all the required tools and dependencies:

```bash
./scripts/install.sh
```

or run the following commands:

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3 python3-pip pipx python-is-python3

pipx install poetry
pipx ensurepath

source ~/.bashrc # or restart terminal

poetry install
```

> Note: This does not work for out of the box on Debian 11 based distros.

## Configuration

To configure the application copy the `.env.example` file to `.env` and change the values as needed.

```bash
cp .env.example .env
```

> Note: The `.env` file should be kept up to date with `.env.example` if any environment variables are added.

## Usage

To run the application, use the following commands:

```bash
poetry run python src/main.py
```

## Updating

To update the repository, use the following commands:

```bash
git pull
poetry update
```

## Development

### Adding dependencies

To add a new dependency, use the following command:

```bash
poetry add <package>
```

### Removing dependencies

To remove a dependency, use the following command:

```bash
poetry remove <package>
```

### Formatting

We use [black](https://black.readthedocs.io/en/stable/) for formatting and [isort](https://pycqa.github.io/isort/) for sorting imports.

```bash
# Raspberry Pi
./scripts/format.sh

# Windows PowerShell
./scripts/format

# Windows Command Prompt
scripts\format

# Or
poetry run isort .
poetry run black .
```

### Linting

We use [flake8](https://flake8.pycqa.org/en/latest/) for linting together with [flake8-bugbear](https://github.com/PyCQA/flake8-bugbear).

```bash
poetry run flake8 . 
```

### Testing

We use [pytest](https://docs.pytest.org/en/stable/) for unit tests.

```bash
poetry run pytest .
```

Will execute all tests in all files whose names follow the form `test_*.py` or `\*_test.py` in the current directory and its subdirectories.

```bash
# Example test that would currently fail
# File: test_sample.py

def inc(x):
    return x + 1

def test_answer():
    assert inc(3) == 5 
```

### Logging

We use [loguru](https://github.com/Delgan/loguru) for logging.

```python
from loguru import logger

logger.info("Hello, World!")
```

Logs are written to the `logs` directory (always with a log level of TRACE) and are printed to the console (log level can be adjusted in `.env`).

The following table shows the severity levels and the corresponding logger methods:

| Level name | Severity value | Logger method |
|------------|----------------|---------------|
| TRACE      | 5              | logger.trace() |
| DEBUG      | 10             | logger.debug() |
| INFO       | 20             | logger.info() |
| SUCCESS    | 25             | logger.success() |
| WARNING    | 30             | logger.warning() |
| ERROR      | 40             | logger.error() |
| CRITICAL   | 50             | logger.critical() |

### Git Hooks

> TODO: Add git hooks for pre-commit formatting and linting to be added.
