#include "calculator.hpp"
#include <iostream>
#include <cstdlib>

int main(int argc, char* argv[]) {
    if (argc != 4) {
       std::cerr << "Usage: ./calculator <operation> <operand1> <operand2>\n"
                  << "Operations:\n"
                  << "  --add        Add two numbers (e.g., ./calculator --add 5 3)\n"
                  << "  --subtract   Subtract the second number from the first (e.g., ./calculator --subtract 5 3)\n"
                  << "  --multiply   Multiply two numbers (e.g., ./calculator --multiply 5 3)\n"
                  << "  --divide     Divide the first number by the second, the second operand must not be zero (e.g., ./calculator --divide 5 3)\n"
                  << "  --modulus    Compute the modulus of the first number by the second, the second operand must not be zero (e.g., ./calculator --modulus 5 3)\n"
                  << "  --power      Raise the first number to the power of the second (e.g., ./calculator --power 5 3)\n"
                  << "Please ensure all operands are valid numbers.\n";        return EXIT_FAILURE;
    }

    double op1 = std::stod(argv[2]);
    double op2 = std::stod(argv[3]);
    std::string operation(argv[1]);

    try {
        double result = calculate(op1, op2, operation);
        std::cout << result << std::endl;
    } catch (const std::exception& e) {
        std::cerr << e.what() << std::endl;
        return EXIT_FAILURE;
    }

    return EXIT_SUCCESS;
}
