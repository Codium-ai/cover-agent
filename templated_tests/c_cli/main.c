#include "calc.h"

int main(int argc, char *argv[]) {
    if (argc != 4) {
        print_usage();
        return 1;
    }

    char* operation = argv[1];
    double op1 = atof(argv[2]);
    double op2 = atof(argv[3]);
    int status = 0;
    double result = calculate(op1, op2, operation, &status);

    switch (status) {
        case 0:  // Success
            if (floor(result) == result) {
                // Result is an integer
                printf("%d\n", (int)result);
            } else {
                // Result is not an integer
                printf("%f\n", result);
            }
            break;
        case 1:  // Division by zero
            fprintf(stderr, "Error: Division by zero\n");
            return 1;
        case 2:  // Unknown operation
            fprintf(stderr, "Invalid operation. Use '--add', '--subtract', '--multiply', '--divide', '--modulus', or '--power'.\n");
            return 1;
        default:
            fprintf(stderr, "An unknown error occurred.\n");
            return 1;
    }

    return 0;
}
