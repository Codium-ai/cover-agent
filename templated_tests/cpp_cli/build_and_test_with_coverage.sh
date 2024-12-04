#!/bin/bash

# Exit on error
set -e

# Compile the test application with Unity and coverage flags
echo "Compiling the test application..."
cmake .
make

# Run the compiled tests and generate coverage data
echo "Running tests..."
./test_calculator

# Capture coverage data and generate reports
echo "Generating coverage reports..."
lcov --capture --directory . --output-file coverage.info --rc lcov_branch_coverage=1
lcov --remove coverage.info '*/usr/*' '*/test_*' --output-file coverage_filtered.info --rc lcov_branch_coverage=1
lcov --list coverage_filtered.info --rc lcov_branch_coverage=1

# convert lcov to cobertura
lcov_cobertura coverage_filtered.info

echo "Test and coverage reporting complete."
