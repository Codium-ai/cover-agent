#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status
set -o pipefail  # Exit if any command in a pipeline fails
set -x  # Print commands and their arguments as they are executed

# Default model name
MODEL="gpt-3.5-turbo"
RUN_INSTALLER=false

# Function to display usage
usage() {
    echo "Usage: $0 [--model model_name] [--run-installer]"
    echo "  --model model_name      Set the model name (default: gpt-3.5-turbo)"
    echo "  --run-installer         Run the installer within a Docker container"
    exit 1
}

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --model)
            MODEL="$2"
            shift
            ;;
        --run-installer)
            RUN_INSTALLER=true
            ;;
        *)
            usage
            ;;
    esac
    shift
done

# Conditional Docker commands
if [ "$RUN_INSTALLER" = true ]; then
    # Get the current user ID and group ID
    USER_ID=$(id -u)
    GROUP_ID=$(id -g)

    # Build the installer within a Docker container
    docker build -t cover-agent-installer -f Dockerfile .

    # Run the Docker container with the current user's ID and group ID
    mkdir -p dist
    docker run --rm --user $USER_ID:$GROUP_ID --volume "$(pwd)/dist:/app/dist" cover-agent-installer
fi

# Python FastAPI Example
sh tests_integration/test_with_docker.sh \
  --dockerfile "templated_tests/python_fastapi/Dockerfile" \
  --source-file-path "app.py" \
  --test-file-path "test_app.py" \
  --test-command "pytest --cov=. --cov-report=xml --cov-report=term" \
  --model $MODEL

# Go Webservice Example
# Note: GPT 3.5 hasn't been powerful enough to generate quality tests that pass
sh tests_integration/test_with_docker.sh \
  --dockerfile "templated_tests/go_webservice/Dockerfile" \
  --source-file-path "app.go" \
  --test-file-path "app_test.go" \
  --test-command "go test -coverprofile=coverage.out && gocov convert coverage.out | gocov-xml > coverage.xml" \
  --model "gpt-4o"

# Java Gradle example
# Note: GPT 3.5 hasn't been powerful enough to generate quality tests that pass
sh tests_integration/test_with_docker.sh \
  --dockerfile "templated_tests/java_gradle/Dockerfile" \
  --source-file-path "src/main/java/com/davidparry/cover/SimpleMathOperations.java" \
  --test-file-path "src/test/groovy/com/davidparry/cover/SimpleMathOperationsSpec.groovy" \
  --test-command "./gradlew clean test jacocoTestReport" \
  --coverage-type "jacoco" \
  --code-coverage-report-path "build/reports/jacoco/test/jacocoTestReport.csv" \
  --model "gpt-4o"

# # Java Spring Calculator example
# sh tests_integration/test_with_docker.sh \
#   --dockerfile "templated_tests/java_spring_calculator/Dockerfile" \
#   --source-file-path "src/main/java/com/example/calculator/controller/CalculatorController.java" \
#   --test-file-path "src/test/java/com/example/calculator/controller/CalculatorControllerTest.java" \
#   --test-command "mvn verify" \
#   --coverage-type "jacoco" \
#   --code-coverage-report-path "target/site/jacoco/jacoco.xml" \
#   --model $MODEL
