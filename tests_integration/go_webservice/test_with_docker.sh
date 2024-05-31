#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status
set -x

# Initialize variables
MODEL=""
API_BASE=""
OPENAI_API_KEY="${OPENAI_API_KEY:-}"

# Function to clean up Docker container
cleanup() {
  if [ -n "$CONTAINER_ID" ]; then
    echo "Cleaning up..."
    docker stop "$CONTAINER_ID" || true
    docker rm "$CONTAINER_ID" || true
  fi
}

# Trap any errors or exits and run cleanup
trap cleanup EXIT

# Parse arguments
while [ "$#" -gt 0 ]; do
  case $1 in
    --model) MODEL="$2"; shift ;;
    --api-base) API_BASE="$2"; shift ;;
    --openai-api-key) OPENAI_API_KEY="$2"; shift ;;
    *) echo "Unknown parameter passed: $1"; exit 1 ;;
  esac
  shift
done

# Build the Docker image
echo "Building the Docker image..."
docker build -t cover-agent-image -f tests_integration/go_webservice/Dockerfile .

# Start the container in detached mode with the environment variable if set
echo "Starting the container..."
if [ -z "$OPENAI_API_KEY" ]; then
  CONTAINER_ID=$(docker run -d cover-agent-image tail -f /dev/null)
else
  CONTAINER_ID=$(docker run -d -e OPENAI_API_KEY="$OPENAI_API_KEY" cover-agent-image tail -f /dev/null)
fi

# Ensure the container started successfully
if [ -z "$CONTAINER_ID" ]; then
  echo "Failed to start the container."
  exit 1
fi

# Copy the cover-agent binary into the running container
echo "Copying cover-agent binary into the container..."
docker cp dist/cover-agent "$CONTAINER_ID":/usr/local/bin/cover-agent

# Run the cover-agent command inside the running container
echo "Running the cover-agent command..."
COMMAND="/usr/local/bin/cover-agent \
  --source-file-path \"app.go\" \
  --test-file-path \"app_test.go\" \
  --code-coverage-report-path \"coverage.xml\" \
  --test-command \"go test -coverprofile=coverage.out && gocov convert coverage.out | gocov-xml > coverage.xml\" \
  --test-command-dir $(pwd) \
  --coverage-type \"cobertura\" \
  --desired-coverage 70 \
  --max-iterations 2"

if [ -n "$MODEL" ]; then
  COMMAND="$COMMAND --model \"$MODEL\""
fi

if [ -n "$API_BASE" ]; then
  COMMAND="$COMMAND --api-base \"$API_BASE\""
fi

if [ -n "$OPENAI_API_KEY" ]; then
  docker exec -e OPENAI_API_KEY="$OPENAI_API_KEY" "$CONTAINER_ID" bash -c "$COMMAND"
else
  docker exec "$CONTAINER_ID" bash -c "$COMMAND"
fi

echo "Done."
