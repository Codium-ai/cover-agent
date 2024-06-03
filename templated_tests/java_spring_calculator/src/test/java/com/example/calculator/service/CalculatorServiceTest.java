package com.example.calculator.service;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

public class CalculatorServiceTest {

    private final CalculatorService calculatorService = new CalculatorService();

    @Test
    public void testAdd() {
        assertEquals(5, calculatorService.add(2, 3));
    }

    @Test
    public void testSubtract() {
        assertEquals(1, calculatorService.subtract(5, 4));
    }

    @Test
    public void testMultiply() {
        assertEquals(6, calculatorService.multiply(2, 3));
    }

    @Test
    public void testDivide() {
        assertEquals(2, calculatorService.divide(6, 3));
    }

    @Test
    public void testDivideByZero() {
        assertThrows(IllegalArgumentException.class, () -> {
            calculatorService.divide(1, 0);
        });
    }
}
