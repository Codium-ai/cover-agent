<div align="center">

<div align="center">


<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://www.codium.ai/images/cover-agent/cover-agent-dark.png" width="330">
  <source media="(prefers-color-scheme: light)" srcset="https://www.codium.ai/images/cover-agent/cover-agent-light.png" width="330">
  <img src="https://www.codium.ai/images/cover-agent/cover-agent-light.png" alt="logo" width="330">

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
- [Installation and Usage](#installation-and-usage)
- [Development](#development)
- [Roadmap](#roadmap)


## News and Updates

### 2024-09-29:
We are excited to announce the latest series of updates to CoverAgent, delivering significant improvements to functionality, documentation, and testing frameworks. These updates reflect our ongoing commitment to enhancing the developer experience, improving error handling, and refining the testing processes.

#### New Features and Enhancements
* Enhanced Database Usage: Introduced a new database_usage.md document outlining the expanded capabilities of logging test results to a structured database.
* Comprehensive System Diagrams: Added a top_level_sequence_diagram.md, providing a clear visual overview of CoverAgent's processes and workflows.
* Docker and Multi-Language Support: Several new Docker configurations and templated tests were introduced for various programming languages, including C#, TypeScript, C, and React, ensuring streamlined testing environments across multiple platforms.
* UnitTestDB Integration: The UnitTestDB.py file was added to support robust logging of test generation attempts, improving error tracking and debugging.

#### Refinements and Modifications
* Coverage Processing: Key improvements to CoverageProcessor.py modularized coverage parsing and expanded support for different coverage report formats (LCOV, Cobertura, Jacoco).
* PromptBuilder Enhancements: New CLI arguments were introduced, including options for running tests multiple times (--run-tests-multiple-times) and a report coverage feature flag for more granular control over coverage behavior.
* CI/CD Pipeline Improvements: Several GitHub workflows were modified to improve pipeline efficiency, including nightly regression tests and templated test publishing pipelines.

#### Improved Documentation
* Detailed Usage Examples: The usage_examples.md file was updated to provide more comprehensive guidance on how to effectively use CoverAgent's features, ensuring that developers can quickly get up to speed with the latest updates.
* Configuration and Template Updates: Configuration files, such as test_generation_prompt.toml, were refined to better support the test framework and eliminate redundant instructions.

These updates signify a major leap forward in improving the ease of use, flexibility, and overall performance of CoverAgent. We are committed to continuing to enhance the tool and providing regular updates based on feedback from our community.

### 2024-06-05:
The logic and prompts for adding new imports for the generated tests have been improved.

We also added a [usage examples](docs/usage_examples.md) file, with more elaborate examples of how to use the Cover Agent.

### 2024-06-01:
Added support for comprehensive logging to [Weights and Biases](https://wandb.ai/). Set the `WANDB_API_KEY` environment variable to enable this feature.

### 2024-05-26:
Cover-Agent now supports nearly any LLM model in the world, using [LiteLLM](#using-other-llms) package.

Notice that GPT-4 outperforms almost any open-source model in the world when it comes to code tasks and following complicated instructions.
However, we updated the post-processing scripts to be more comprehensive, and were able to successfully run the [baseline script](#running-the-code) with `llama3-8B` and `llama3-70B models`, for example.

### 2024-05-09: 
This repository includes the first known implementation of TestGen-LLM, described in the paper [Automated Unit Test Improvement using Large Language Models at Meta](https://arxiv.org/abs/2402.09171).

# Cover-Agent
Welcome to Cover-Agent. This focused project utilizes Generative AI to automate and enhance the generation of tests (currently mostly unit tests), aiming to streamline development workflows. Cover-Agent can run via a terminal, and is planned to be integrated into popular CI platforms.
[![Test generation xxx](https://www.codium.ai/wp-content/uploads/2024/05/CodiumAI-CoverAgent-v240519-small-loop.gif)](https://youtu.be/fIYkSEJ4eqE?feature=shared)

We invite the community to collaborate and help extend the capabilities of Cover Agent, continuing its development as a cutting-edge solution in the automated unit test generation domain. We also wish to inspire researchers to leverage this open-source tool to explore new test-generation techniques.


## Overview
This tool is part of a broader suite of utilities designed to automate the creation of unit tests for software projects. Utilizing advanced Generative AI models, it aims to simplify and expedite the testing process, ensuring high-quality software development. The system comprises several components:
1. **Test Runner:** Executes the command or scripts to run the test suite and generate code coverage reports.
2. **Coverage Parser:** Validates that code coverage increases as tests are added, ensuring that new tests contribute to the overall test effectiveness.
3. **Prompt Builder:** Gathers necessary data from the codebase and constructs the prompt to be passed to the Large Language Model (LLM).
4. **AI Caller:** Interacts with the LLM to generate tests based on the prompt provided.

## Installation and Usage
### Requirements
Before you begin, make sure you have the following:
- `OPENAI_API_KEY` set in your environment variables, which is required for calling the OpenAI API.
- Code Coverage tool: A Cobertura XML code coverage report is required for the tool to function correctly.
  - For example, in Python one could use `pytest-cov`. Add the `--cov-report=xml` option when running Pytest.
  - Note: We are actively working on adding more coverage types but please feel free to open a PR and contribute to `cover_agent/CoverageProcessor.py`

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

You can use the example code below to try out the Cover Agent.
(Note that the [usage_examples](docs/usage_examples.md) file provides more elaborate examples of how to use the Cover Agent)

#### Python

Follow the steps in the README.md file located in the `templated_tests/python_fastapi/` directory to setup an environment, then return to the root of the repository, and run the following command to add tests to the **python fastapi** example:
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

#### Go

For an example using **go** `cd` into `templated_tests/go_webservice`, set up the project following the `README.md`.
To work with coverage reporting, you need to install `gocov` and `gocov-xml`. Run the following commands to install these tools:
```shell
go install github.com/axw/gocov/gocov@v1.1.0
go install github.com/AlekSi/gocov-xml@v1.1.0
```
and then run the following command:
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

#### Java
For an example using **java** `cd` into `templated_tests/java_gradle`, set up the project following the [README.md](templated_tests/java_gradle/README.md).
To work with jacoco coverage reporting, follow the [README.md](templated_tests/java_gradle/README.md) Requirements section:
and then run the following command:
```shell
cover-agent \
  --source-file-path="src/main/java/com/davidparry/cover/SimpleMathOperations.java" \
  --test-file-path="src/test/groovy/com/davidparry/cover/SimpleMathOperationsSpec.groovy" \
  --code-coverage-report-path="build/reports/jacoco/test/jacocoTestReport.csv" \
  --test-command="./gradlew clean test jacocoTestReport" \
  --test-command-dir=$(pwd) \
  --coverage-type="jacoco" \
  --desired-coverage=70 \
  --max-iterations=1
```

### Outputs
A few debug files will be outputted locally within the repository (that are part of the `.gitignore`)
* `run.log`: A copy of the logger that gets dumped to your `stdout`
* `test_results.html`: A results table that contains the following for each generated test:
  * Test status
  * Failure reason (if applicable)
  * Exit code, 
  * `stderr`
  * `stdout`
  * Generated test

### Additional logging
If you set an environment variable `WANDB_API_KEY`, the prompts, responses, and additional information will be logged to [Weights and Biases](https://wandb.ai/).

### Using other LLMs
This project uses LiteLLM to communicate with OpenAI and other hosted LLMs (supporting 100+ LLMs to date). To use a different model other than the OpenAI default you'll need to:
1. Export any environment variables needed by the supported LLM [following the LiteLLM instructions](https://litellm.vercel.app/docs/proxy/quick_start#supported-llms).
2. Call the name of the model using the `--model` option when calling Cover Agent.

For example (as found in the [LiteLLM Quick Start guide](https://litellm.vercel.app/docs/proxy/quick_start#supported-llms)):
```shell
export VERTEX_PROJECT="hardy-project"
export VERTEX_LOCATION="us-west"

cover-agent \
  ...
  --model "vertex_ai/gemini-pro"
```

#### OpenAI Compatible Endpoint
```shell
export OPENAI_API_KEY="<your api key>" # If <your-api-base> requires an API KEY, set this value.

cover-agent \
  ...
  --model "openai/<your model name>" \
  --api-base "<your-api-base>"
```


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

### Building the binary locally
You can build the binary locally simply by invoking the `make installer` command. This will run PyInstaller locally on your machine. Ensure that you have set up the poetry project first (i.e. running `poetry install`).

## Roadmap
Below is the roadmap of planned features, with the current implementation status:

- [x] Automatically generates unit tests for your software projects, utilizing advanced AI models to ensure comprehensive test coverage and quality assurance. (similar to Meta)
  - [x] Being able to generate tests for different programming languages
  - [ ] Being able to deal with a large variety of testing scenarios
  - [ ] Generate a behavior analysis for the code under test, and generate tests accordingly
  - [x] Check test flakiness, e.g. by running 5 times as suggested by TestGen-LLM
- [ ] Cover more test generation pains
  - [ ] Generate new tests that are focused on the PR changeset
  - [ ] Run over an entire repo/code-base and attempt to enhance all existing test suites
- [ ] Improve usability
  - [ ] Connectors for GitHub Actions, Jenkins, CircleCI, Travis CI, and more
  - [ ] Integrate into databases, APIs, OpenTelemetry and other sources of data to extract relevant i/o for the test generation
  - [ ] Add a setting file

## CodiumAI
CodiumAI's mission is to enable busy dev teams to increase and maintain their code integrity.
We offer various tools, including "Pro" versions of our open-source tools, which are meant to handle enterprise-level code complexity and are multi-repo codebase aware.
