# Use an image with the required GLIBC version
FROM ubuntu:24.04 as builder

# Install Java, Python 3.12, and its dev dependencies
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y \
    wget \
    unzip \
    openjdk-11-jdk && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install specific Gradle version
RUN wget https://services.gradle.org/distributions/gradle-7.2-bin.zip -P /tmp && \
    unzip -d /opt/gradle /tmp/gradle-*.zip && \
    ls /opt/gradle/gradle-* && \
    echo "export GRADLE_HOME=/opt/gradle/gradle-7.2" >> /etc/profile.d/gradle.sh && \
    echo "export PATH=\${GRADLE_HOME}/bin:\${PATH}" >> /etc/profile.d/gradle.sh && \
    chmod +x /etc/profile.d/gradle.sh && \
    . /etc/profile.d/gradle.sh

# Set the environment variable for all subsequent RUN commands
ENV PATH="/opt/gradle/gradle-7.2/bin:${PATH}"

# Set the working directory
WORKDIR /home/gradle/src

# Copy the Gradle configuration files into the Docker image
COPY build.gradle settings.gradle gradlew ./

RUN chmod +x ./gradlew

# Copy the source code into the Docker image
COPY src ./src
COPY gradle ./gradle

# Build the application
RUN gradle build --no-daemon