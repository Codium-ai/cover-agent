# Integration Tests for Cover Agent
This folder contains end-to-end integration tests for Cover Agent.

## Prerequisites
Before running any of these tests, you will need to build the installer package by running the following command from the root of the repository:
```
make installer
```

You will also need [Docker](https://www.docker.com/) installed.

__Note:__ These scripts were written for Linux but have been tested on a Windows system using WSL 2 and Docker for Desktop.

Since the targets live in Linux, you'll need to build the installer in Linux (versus on Windows and MacOS). This can be done automatically in the `sh tests_integration/test_all.sh` script by adding the `--run-installer` flag.

## How to Run
You can run these example test suites using a locally hosted LLM or in the cloud just as you would normally with Cover Agent.

### Running the Tests
To run the full test suite, simply run the following command from the root of the repository:
```
sh tests_integration/test_all.sh
```

Or run each test individually:
#### Python Fast API Example
```
sh tests_integration/test_with_docker.sh \
  --dockerfile "templated_tests/python_fastapi/Dockerfile" \
  --source-file-path "app.py" \
  --test-file-path "test_app.py" \
  --test-command "pytest --cov=. --cov-report=xml --cov-report=term"
```

#### Go Webservice Example
```
sh tests_integration/test_with_docker.sh \
  --dockerfile "templated_tests/go_webservice/Dockerfile" \
  --source-file-path "app.go" \
  --test-file-path "app_test.go" \
  --test-command "go test -coverprofile=coverage.out && gocov convert coverage.out | gocov-xml > coverage.xml" \
  --model "gpt-4o"
```

#### Java Gradle Example
```
sh tests_integration/test_with_docker.sh \
  --dockerfile "templated_tests/java_gradle/Dockerfile" \
  --source-file-path "src/main/java/com/davidparry/cover/SimpleMathOperations.java" \
  --test-file-path "src/test/groovy/com/davidparry/cover/SimpleMathOperationsSpec.groovy" \
  --test-command "./gradlew clean test jacocoTestReport" \
  --coverage-type "jacoco" \
  --code-coverage-report-path "build/reports/jacoco/test/jacocoTestReport.csv" \
  --model "gpt-4o"
```

#### Java Spring Calculator Example
```
sh tests_integration/test_with_docker.sh \
  --dockerfile "templated_tests/java_spring_calculator/Dockerfile" \
  --source-file-path "src/main/java/com/example/calculator/controller/CalculatorController.java" \
  --test-file-path "src/test/java/com/example/calculator/controller/CalculatorControllerTest.java" \
  --test-command "mvn verify" \
  --coverage-type "jacoco" \
  --code-coverage-report-path "target/site/jacoco/jacoco.csv" \
  --model "gpt-4o"
```

#### VanillaJS Example
```
sh tests_integration/test_with_docker.sh \
  --dockerfile "templated_tests/js_vanilla/Dockerfile" \
  --source-file-path "ui.js" \
  --test-file-path "ui.test.js" \
  --test-command "npm run test:coverage" \
  --code-coverage-report-path "coverage/coverage.xml" \
  --model "gpt-4o"
```

### Using Different LLMs
You can use a different LLM by passing in the `--model` and `--api-base` parameters. For example, to use a locally hosted LLM with Ollama you can pass in:
```
--model "ollama/mistral" --api-base "http://host.docker.internal:11434"
```

For any other LLM that requires more environment variables to be set, you will need to update the shell script and pass in the variables within the Docker command.

## When to Run
This test suite is intended to run with real LLMs (either locally hosted or online). If choosing cloud-provided LLMs, keep in mind that there is a cost associated with running these tests.

These tests should **absolutely** be run before a massive refactor or any major changes to the LLM/prompting logic of the code.

## How It Works
The integration tests run within Docker containers to ensure complete isolation from any external or existing environment.

# Increasing Coverage Iteratively
The `increase_coverage.py` script attempts to run Cover Agent for all files within the `cover_agent` directory. You'll need to call a Poetry shell first before running like so:
```
poetry install
poetry shell
python tests_integration/increase_coverage.py
```