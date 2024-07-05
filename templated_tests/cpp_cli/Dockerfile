FROM gcc:14

# Install build tools
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    software-properties-common \
    g++ \
    cmake \
    make \
    lcov

# Add the Ubuntu Toolchain PPA and upgrade libstdc++
RUN add-apt-repository ppa:ubuntu-toolchain-r/test
RUN apt-get update && apt-get upgrade -y libstdc++6

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
