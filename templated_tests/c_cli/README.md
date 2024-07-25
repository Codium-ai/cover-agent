# Calculator Program
Simple command-line calculator for basic arithmetic operations.

## Prerequisites
Install GCC, Ruby, lcov, lcov-cobertura (until lcov is natively supported), and clone the Unity test framework:

```bash
sudo apt-get update
sudo apt-get install gcc ruby lcov
pip install lcov_cobertura
git clone https://github.com/ThrowTheSwitch/Unity.git
```

## Compile and Run
Compile the calculator:

```bash
gcc -o calculator main.c calc.c -lm
```

Run the calculator:

```bash
./calculator # get usage
./calculator --add 5 3  # Replace `--add 5 3` with your operation and operands
```

## Testing
Generate the test runner using the Ruby script from Unity:

```bash
ruby Unity/auto/generate_test_runner.rb test_calc.c test_calc_Runner.c
```

Compile the tests with coverage:

```bash
gcc -o calc_tests test_calc.c test_calc_Runner.c Unity/src/unity.c calc.c -lm -IUnity/src -fprofile-arcs -ftest-coverage
```

Run tests and generate coverage report:

```bash
./calc_tests
lcov --capture --directory . --output-file coverage.info
lcov --remove coverage.info '*/Unity/*' '*/test_*' --output-file coverage_filtered.info
lcov --list coverage_filtered.info
```

See `build_and_test_with_coverage.sh` for a complete script to build and run the tests with coverage
