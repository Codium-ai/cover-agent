# Integration tests for Cover Agent
This folder contains end-to-end integration tests for Cover Agent

## Prerequisites
Before running any of these tests you will need to build the installer package by running the following command from the root of the repository:
```
make installer
```

You will also need [Docker](https://www.docker.com/) installed.

Note: These scripts were written for Linux but they have been tested on a Windows system using WSL 2 and Docker for Desktop.

## How to run
You can run these example test suites using a locally hosted LLM or in the cloud just as you would normally with Cover Agent

### Python Fast API Example
From the root of the repository run the following command:
```
sh tests_integration/python_fastapi/test_openai.sh
```

You can use a different LLM by passing in the `--model` and `--api-base` parameters. For example, to use a locally hosted LLM with Ollama you can pass in:
```
--model "ollama/mistral" --api-base "http://host.docker.internal:11434"
```

For any other LLM that requires more environment variables to be set you will need to update the shell script and pass in the variables within the Docker command.

## When to run
This test suite is intended to run with real LLMs (either locally hosted on online). If choosing cloud provided LLMs keep in mind that there is a cost associated with running these tests.

These tests should **absolutely** be run before a massive refactor or any major changes to the LLM/prompting logic of the code.

## How it works
The integration tests run within Docker containers in order to prove out complete isolation from any external or existing environment