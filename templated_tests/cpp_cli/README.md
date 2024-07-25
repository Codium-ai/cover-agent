# Calculator Program
Simple command-line calculator for basic arithmetic operations.

## Prerequisites
Install g++, make, gtest, lcov, lcov-cobertura (until lcov is natively supported):

```bash
sudo apt-get update
sudo apt-get install g++ cmake make lcov libgtest-dev
pip install lcov_cobertura
```

Build Google Test

```bash
cd /usr/src/gtest
sudo cmake CMakeLists.txt
sudo make
sudo find . -type f -name "*.a" -exec cp {} /usr/lib \;
```

## Compile and Run
Compile the calculator:

```bash
cmake .
make
```

Run the calculator:

```bash
./calculator # get usage
./calculator --add 5 3  # Replace `--add 5 3` with your operation and operands
```

## Testing
Compile the tests with coverage:

```bash
cmake .
make
```

Run tests and generate coverage report:

```bash
./test_calculator
lcov --capture --directory . --output-file coverage.info
lcov --remove coverage.info '/usr/*' '*/test_*' --output-file coverage_filtered.info
lcov --list coverage_filtered.info
```

See `build_and_test_with_coverage.sh` for a complete script to build and run the tests with coverage
