FROM python:3

# Install build tools
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y g++ cmake make lcov

# install packages for code coverage
RUN pip install lcov_cobertura

# Install Google Test source
RUN apt-get install -y libgtest-dev

# Build Google Test
WORKDIR /usr/src/gtest
RUN cmake CMakeLists.txt
RUN make

# Copy the library files to a standard library location (if they exist)
RUN find . -type f -name "*.a" -exec cp {} /usr/lib \;

# Set up the project directory
WORKDIR /app
COPY . /app
