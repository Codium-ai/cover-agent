#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status

# Ensure OPENAI_API_KEY is set
if [ -z "$OPENAI_API_KEY" ]; then
  echo "Error: OPENAI_API_KEY is not set."
  exit 1
fi

# Build the Docker image
echo "Building the Docker image..."
docker build -t cover-agent-image -f tests_integration/python_fastapi/Dockerfile .

# Start the container in detached mode with the environment variable
echo "Starting the container..."
CONTAINER_ID=$(docker run -d -e OPENAI_API_KEY=$OPENAI_API_KEY cover-agent-image tail -f /dev/null)

# Ensure the container started successfully
if [ -z "$CONTAINER_ID" ]; then
  echo "Failed to start the container."
  exit 1
fi

# Copy the cover-agent binary into the running container
echo "Copying cover-agent binary into the container..."
docker cp dist/cover-agent $CONTAINER_ID:/usr/local/bin/cover-agent

# Run the cover-agent command inside the running container
echo "Running the cover-agent command..."
docker exec -e OPENAI_API_KEY=$OPENAI_API_KEY $CONTAINER_ID /usr/local/bin/cover-agent \
  --source-file-path "app.py" \
  --test-file-path "test_app.py" \
  --code-coverage-report-path "coverage.xml" \
  --test-command "pytest --cov=. --cov-report=xml --cov-report=term" \
  --coverage-type "cobertura" \
  --desired-coverage 70 \
  --max-iterations 10

# Clean up by stopping and removing the container
echo "Cleaning up..."
docker stop $CONTAINER_ID
docker rm $CONTAINER_ID

echo "Done."
