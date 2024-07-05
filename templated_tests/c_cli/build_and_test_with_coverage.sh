#!/bin/bash

# Exit on error
set -e

# Check for required commands
command -v ruby >/dev/null 2>&1 || { echo >&2 "Ruby is required but it's not installed. Aborting."; exit 1; }
command -v gcc >/dev/null 2>&1 || { echo >&2 "GCC is required but it's not installed. Aborting."; exit 1; }

# Generate the test runner using the Ruby script from Unity
echo "Generating test runner..."
ruby Unity/auto/generate_test_runner.rb test_calc.c test_calc_Runner.c

# Compile the test application with Unity and coverage flags
echo "Compiling the test application..."
gcc -o test_calc test_calc.c test_calc_Runner.c Unity/src/unity.c calc.c -lm -IUnity/src -fprofile-arcs -ftest-coverage

# Run the compiled tests and generate coverage data
echo "Running tests..."
./test_calc

# Capture coverage data and generate reports
echo "Generating coverage reports..."
lcov --capture --directory . --output-file coverage.info
lcov --remove coverage.info '*/Unity/*' '*/test_*' --output-file coverage_filtered.info
lcov --list coverage_filtered.info

# convert lcov to cobertura
lcov_cobertura coverage_filtered.info

echo "Test and coverage reporting complete."
