#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status
set -o pipefail  # Exit if any command in a pipeline fails
set -x  # Print commands and their arguments as they are executed

# Set model name
MODEL="gpt-3.5-turbo"

# Python FastAPI Example
sh tests_integration/test_with_docker.sh \
  --dockerfile "tests_integration/python_fastapi/Dockerfile" \
  --source-file-path "app.py" \
  --test-file-path "test_app.py" \
  --test-command "pytest --cov=. --cov-report=xml --cov-report=term" \
  --model $MODEL

# Go Webservice Example
sh tests_integration/test_with_docker.sh \
  --dockerfile "tests_integration/go_webservice/Dockerfile" \
  --source-file-path "app.go" \
  --test-file-path "app_test.go" \
  --test-command "go test -coverprofile=coverage.out && gocov convert coverage.out | gocov-xml > coverage.xml" \
  --model $MODEL