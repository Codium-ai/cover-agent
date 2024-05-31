#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status
set -o pipefail  # Exit if any command in a pipeline fails
set -x  # Print commands and their arguments as they are executed

# Set model name
MODEL="gpt-3.5-turbo"


# Run the Python FastAPI Example project
sh tests_integration/python_fastapi/test_with_docker.sh --model $MODEL
sh tests_integration/go_webservice/test_with_docker.sh --model $MODEL