#include "unity.h"
#include "calc.h"

void test_Addition(void) {
    int status;
    double result = calculate(5, 3, "--add", &status);
    TEST_ASSERT_EQUAL_INT(8, result);
    TEST_ASSERT_EQUAL_INT(0, status);
}