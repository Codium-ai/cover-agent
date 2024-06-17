FROM maven:latest

# Set the working directory inside the container
WORKDIR /app

# Install glibc
RUN apt-get update && \
    apt-get install -y libc6

# Copy the pom.xml file and the source code
COPY pom.xml .
COPY src ./src

# Package the application and run tests
RUN mvn clean verify
