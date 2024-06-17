package com.example.calculator.controller;

import com.example.calculator.controller.CalculatorController;
import com.example.calculator.service.CalculatorService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.web.servlet.MockMvc;

import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;

@WebMvcTest(CalculatorController.class)
public class CalculatorControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private CalculatorService calculatorService;

    @BeforeEach
    public void setUp() {
        when(calculatorService.add(2, 3)).thenReturn(5.0);
        when(calculatorService.subtract(5, 4)).thenReturn(1.0);
        when(calculatorService.multiply(2, 3)).thenReturn(6.0);
        when(calculatorService.divide(6, 3)).thenReturn(2.0);
    }

    @Test
    public void testAdd() throws Exception {
        mockMvc.perform(get("/add?a=2&b=3"))
                .andExpect(status().isOk())
                .andExpect(content().string("5.0"));
    }

    @Test
    public void testSubtract() throws Exception {
        mockMvc.perform(get("/subtract?a=5&b=4"))
                .andExpect(status().isOk())
                .andExpect(content().string("1.0"));
    }

}
