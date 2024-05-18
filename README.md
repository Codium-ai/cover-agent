<div align="center">

<div align="center">


<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://codium.ai/images/pr_agent/logo-dark.png" width="330">
  <source media="(prefers-color-scheme: light)" srcset="https://codium.ai/images/pr_agent/logo-light.png" width="330">
  <img src="https://codium.ai/images/pr_agent/logo-light.png" alt="logo" width="330">

</picture>
<br/>
CodiumAI Cover Agent aims to help efficiently increasing code coverage, by automatically generating qualified tests to enhance existing test suites
</div>

[![GitHub license](https://img.shields.io/badge/License-AGPL_3.0-blue.svg)](https://github.com/Codium-ai/cover-agent/blob/main/LICENSE)
[![Discord](https://badgen.net/badge/icon/discord?icon=discord&label&color=purple)](https://discord.gg/cYsvFJJbdM)
[![Twitter](https://img.shields.io/twitter/follow/codiumai)](https://twitter.com/codiumai)
    <a href="https://github.com/Codium-ai/cover-agent/commits/main">
    <img alt="GitHub" src="https://img.shields.io/github/last-commit/Codium-ai/cover-agent/main?style=for-the-badge" height="20">
    </a>
</div>

## Table of Contents
- [News and Updates](#news-and-updates)
- [Overview](#overview)
- [Usage](#usage)
- [Roadmap](#roadmap)


## News and Updates
### 2024-05-09: 
#### This repository hosts the implementation of Cover Agent, an open-source project inspired by the innovative techniques described in the paper [Automated Unit Test Improvement using Large Language Models](https://arxiv.org/abs/2402.09171) at Meta.

# Cover-Agent
Welcome to Cover-Agent. This focused project utilizes Generative AI to automate and enhance the generation of unit tests, aiming to streamline development workflows. Cover Agent can be integrated into popular CI platforms or run via a terminal, making it a critical asset for any software development team.

We invite the open-source community to collaborate and help extend the capabilities of Cover Agent, continuing its development as a cutting-edge solution in the domain of automated unit test generation.

## Overview
This tool is part of a broader suite of utilities designed to automate the creation of unit tests for software projects. Utilizing advanced Generative AI models, it aims to simplify and expedite the testing process, ensuring high-quality software development. The system comprises several components:
1. **Test Runner:** Executes the command or scripts to run the test suite and generate code coverage reports.
2. **Coverage Parser:** Validates that code coverage is increasing as tests are added, ensuring that new tests are contributing to the overall test effectiveness.
3. **Prompt Builder:** Gathers necessary data from the codebase and constructs the prompt to be passed to the Large Language Model (LLM).
4. **AI Caller:** Interacts with the LLM to generate tests based on the prompt provided.

## Usage
### Requirements
Before you begin, make sure you have the following:
- `OPENAI_API_KEY` set in your environment variables, which is required for calling the OpenAI API.

If running directly from the repository you will also need:
- Python installed on your system.
- Poetry installed for managing Python package dependencies. Installation instructions for Poetry can be found at [https://python-poetry.org/docs/](https://python-poetry.org/docs/).

### Standalone Runtime
The Cover Agent can be installed as a Python Pip package or run as a standalone executable.

#### Python Pip
To install the Python Pip package directly via GitHub run the following command:
```
pip install git+https://github.com/Codium-ai/cover-agent.git
```

#### Binary
The binary can be run without any Python environment installed on your system (e.g. within a Docker container that does not contain Python). You can download the release for your system by navigating to the project's [release page](https://github.com/Codium-ai/cover-agent/releases).

### Repository Setup
Run the following command to install all the dependencies and run the project from source:
```shell
poetry install
```

### Running the Code
After downloading the executable or installing the Pip package you can run the Cover Agent to generate and validate unit tests. Execute it from the command line by using the following command:
```shell
cover-agent \
  --source-file-path "<path_to_source_file>" \
  --test-file-path "<path_to_test_file>" \
  --code-coverage-report-path "<path_to_coverage_report>" \
  --test-command "<test_command_to_run>" \
  --test-command-dir "<directory_to_run_test_command>" \
  --coverage-type "<type_of_coverage_report>" \
  --desired-coverage <desired_coverage_between_0_and_100> \
  --max-iterations <max_number_of_llm_iterations> \
  --included-files "<optional_list_of_files_to_include>"
```

You can use the example projects within this repository to run this code as a test.

Run the following command from the root of this repository to add tests to the python fastapi example:
```shell
cover-agent \
  --source-file-path "templated_tests/python_fastapi/app.py" \
  --test-file-path "templated_tests/python_fastapi/test_app.py" \
  --code-coverage-report-path "templated_tests/python_fastapi/coverage.xml" \
  --test-command "pytest --cov=. --cov-report=xml --cov-report=term" \
  --test-command-dir "templated_tests/python_fastapi" \
  --coverage-type "cobertura" \
  --desired-coverage 70 \
  --max-iterations 10
```

For an example using Go `cd` into `templated_tests/go_webservice`, set up the project following the `README.md` and then run the following command:
```shell
cover-agent \
  --source-file-path "app.go" \
  --test-file-path "app_test.go" \
  --code-coverage-report-path "coverage.xml" \
  --test-command "go test -coverprofile=coverage.out && gocov convert coverage.out | gocov-xml > coverage.xml" \
  --test-command-dir $(pwd) \
  --coverage-type "cobertura" \
  --desired-coverage 70 \
  --max-iterations 1
```

Try and add more tests to this project by running this command at the root of this repository:
```shell
poetry run cover-agent \
  --source-file-path "cover_agent/main.py" \
  --test-file-path "tests/test_main.py" \
  --code-coverage-report-path "coverage.xml" \
  --test-command "poetry run pytest --junitxml=testLog.xml --cov=templated_tests --cov=cover_agent --cov-report=xml --cov-report=term --log-cli-level=INFO" \
  --coverage-type "cobertura" \
  --desired-coverage 70 \
  --max-iterations 1 \
  --openai-model "gpt-4o" \
  --additional-instructions "Since I am using a test class each line of code (including the first line), In your response, will need to be prepended with 4 whitespaces. This is extremely important to check to make sure every line returned contains that 4 whitespace indent otherwise my code will not run."
```

Note: If you are using Poetry then use the `poetry run python -m cover-agent` command instead of the `cover-agent` run command.

### Outputs
A few debug files will be outputted locally within the repository (that are part of the `.gitignore`)
* `generated_prompt.md`: The full prompt that is sent to the LLM
* `run.log`: A copy of the logger that gets dumped to your `stdout`
* `test_results.html`: A results table that contains the following for each generated test:
  * Test status
  * Failure reason (if applicable)
  * Exit code, 
  * `stderr`
  * `stdout`
  * Generated test

## Development
This section discusses the development of this project.

### Versioning
Before merging to main make sure to manually increment the version number in `cover_agent/version.txt` at the root of the repository.

### Running Tests
Set up your development environment by running the `poetry install` command as you did above. 

Note: for older versions of Poetry you may need to include the `--dev` option to install Dev dependencies.

After setting up your environment run the following command:
```
poetry run pytest --junitxml=testLog.xml --cov=templated_tests --cov=cover_agent --cov-report=xml --cov-report=term --log-cli-level=INFO
```
This will also generate all logs and output reports that are generated in `.github/workflows/ci_pipeline.yml`.

## Roadmap
Below is the roadmap of planned features, with the current implementation status:

- [x] Automatically generates unit tests for your software projects, utilizing advanced AI models to ensure comprehensive test coverage and quality assurance. (similar to Meta)
  - [x] Being able to generate tests for different programming languages
  - [ ] Being able to deal with a large variety of testing scenarios
- [ ] Generate new tests that are focused on the PR changeset
- [ ] [TODO] Cover more test generation pains
- [ ] Connectors for GitHub Actions, Jenkins, CircleCI, Travis CI, and more
