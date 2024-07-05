#include "calc.h"

double calculate(double op1, double op2, const char* operation, int* status) {
    *status = 0;  // Assume success initially
    if (strcmp(operation, "--add") == 0) {
        return op1 + op2;
    } else if (strcmp(operation, "--subtract") == 0) {
        return op1 - op2;
    } else if (strcmp(operation, "--multiply") == 0) {
        return op1 * op2;
    } else if (strcmp(operation, "--divide") == 0) {
        if (op2 == 0) {
            *status = 1;  // Error: Division by zero
            return 0;
        }
        return op1 / op2;
    } else if (strcmp(operation, "--modulus") == 0) {
        if ((int)op2 == 0) {
            *status = 1;  // Error: Division by zero for modulus
            return 0;
        }
        return (int)op1 % (int)op2;
    } else if (strcmp(operation, "--power") == 0) {
        return pow(op1, op2);
    } else {
        *status = 2;  // Error: Unknown operation
        return 0;
    }
}

void print_usage() {
    printf("Usage: ./calc <operation> <first operand> <second operand>\n");
    printf("Operations:\n");
    printf("  --add:       Add two numbers. Example: ./calc --add 5 3\n");
    printf("  --subtract:  Subtract the second number from the first. Example: ./calc --subtract 5 3\n");
    printf("  --multiply:  Multiply two numbers. Example: ./calc --multiply 5 3\n");
    printf("  --divide:    Divide the first number by the second. Example: ./calc --divide 5 3 (Note: The second operand cannot be zero.)\n");
    printf("  --modulus:   Compute the modulus of the first number by the second. Example: ./calc --modulus 5 3 (Note: The second operand cannot be zero.)\n");
    printf("  --power:     Raise the first number to the power of the second. Example: ./calc --power 5 3\n");
}
