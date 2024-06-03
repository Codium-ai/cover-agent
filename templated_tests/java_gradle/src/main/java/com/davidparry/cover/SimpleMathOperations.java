package com.davidparry.cover;

import com.davidparry.cover.imp.Fibonacci;

public class SimpleMathOperations {

    private final Fibonacci fibonacci;

    public SimpleMathOperations(Fibonacci fibonacci) {
        this.fibonacci = fibonacci;
    }

    public int add(int a, int b) {
        return a + b;
    }

    public int subtract(int a, int b) {
        return a - b;
    }

    public int multiply(int a, int b) {
        return a * b;
    }

    public double divide(int a, int b) {
        if (b == 0) {
            throw new IllegalArgumentException("Division by zero is not allowed.");
        }
        return (double) a / b;
    }

    public int fibonacci(int n) {
        return fibonacci.calculate(n);
    }
}