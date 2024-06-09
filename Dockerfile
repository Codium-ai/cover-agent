# Dockerfile to build installer for Cover Agent
FROM python:3.12

WORKDIR /app

# Copy all files
COPY . .

# Install required packages
RUN pip install poetry wandb
RUN poetry install

# Run the make installer as a CMD
CMD ["make", "installer"]