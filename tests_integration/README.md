# Integration tests for Cover Agent
This folder contains end-to-end integration tests for Cover Agent

## How to run

## When to run
This test suite is intended to run with real LLMs (either locally hosted on online). If choosing cloud provided LLMs keep in mind that there is a cost associated with running these tests.

These tests should **absolutely** be run before a massive refactor or any major changes to the LLM/prompting logic of the code.

## How it works
The integration tests run within Docker containers in order to prove out complete isolation from any external or existing environment