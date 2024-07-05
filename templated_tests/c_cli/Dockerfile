FROM python:3

# Install necessary packages including lcov for coverage reporting
RUN apt-get update && \
    apt-get install -y curl unzip ruby lcov
RUN pip install lcov_cobertura

# Set up the working directory
WORKDIR /usr/src/myapp

# Download and unzip Unity from GitHub
RUN curl -L https://github.com/ThrowTheSwitch/Unity/archive/master.zip -o unity-master.zip && \
    unzip unity-master.zip && \
    mv Unity-master Unity && \
    rm unity-master.zip

# Copy project files
COPY . /usr/src/myapp/