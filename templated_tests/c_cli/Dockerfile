FROM gcc:14

# Install necessary packages including lcov for coverage reporting
RUN apt-get update && \
    apt-get install -y curl unzip ruby lcov

# Set up the working directory
WORKDIR /usr/src/myapp

# Download and unzip Unity from GitHub
RUN curl -L https://github.com/ThrowTheSwitch/Unity/archive/master.zip -o unity-master.zip && \
    unzip unity-master.zip && \
    mv Unity-master Unity && \
    rm unity-master.zip

# Copy project files
COPY . /usr/src/myapp/

# Generate test runner (assuming your script and tests are already in the copied project files)
RUN ruby Unity/auto/generate_test_runner.rb test_calc.c test_calc_Runner.c

# Compile the test application including the directory of the Unity header files
# and coverage flags
RUN gcc -o test_calc test_calc.c test_calc_Runner.c Unity/src/unity.c calc.c -lm -IUnity/src -fprofile-arcs -ftest-coverage

# # Entry point runs the test and captures coverage data
# ENTRYPOINT ["sh", "-c", "./test_calc && \
#                         lcov --capture --directory . --output-file coverage.info && \
#                         lcov --remove coverage.info '*/Unity/*' '*/test_*' --output-file coverage_filtered.info && \
#                         lcov --list coverage_filtered.info"]
# CMD []