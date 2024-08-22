#include "calculator.hpp"
#include <cmath>
#include <stdexcept>

double calculate(double op1, double op2, const std::string& operation) {
    if (operation == "--add") {
        return op1 + op2;
    } else if (operation == "--subtract") {
        return op1 - op2;
    } else if (operation == "--multiply") {
        return op1 * op2;
    } else if (operation == "--divide") {
        if (op2 == 0) throw std::invalid_argument("Division by zero");
        return op1 / op2;
    } else if (operation == "--modulus") {
        if (op2 == 0) throw std::invalid_argument("Division by zero");
        return std::fmod(op1, op2);
    } else if (operation == "--power") {
        return std::pow(op1, op2);
    } else {
        throw std::invalid_argument("Unsupported operation");
    }
}
