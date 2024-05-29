package com.davidparry.cover

import spock.lang.Specification

class SimpleMathOperationsSpec extends Specification {

    def "should return correct sum when adding two positive integers"() {
        given:
        SimpleMathOperations operations = new SimpleMathOperations()

        when:
        int result = operations.add(5, 3)

        then:
        assert result == 8
    }

    def "should return correct result when subtracting two positive integers"() {
        given:
        SimpleMathOperations operations = new SimpleMathOperations()

        when:
        int result = operations.subtract(10, 5)

        then:
        assert result == 5
    }

    def "should return correct value for fibonacci sequence"() {
        given:
        SimpleMathOperations operations = new SimpleMathOperations()
    
        when:
        int result = operations.fibonacci(5)
    
        then:
        assert result == 5
    }


    def "should throw IllegalArgumentException when dividing by zero"() {
        given:
        SimpleMathOperations operations = new SimpleMathOperations()
    
        when:
        operations.divide(10, 0)
    
        then:
        thrown(IllegalArgumentException)
    }


    def "should return correct quotient when dividing two positive integers"() {
        given:
        SimpleMathOperations operations = new SimpleMathOperations()
    
        when:
        double result = operations.divide(10, 2)
    
        then:
        assert result == 5.0
    }


    def "should return correct product when multiplying two positive integers"() {
        given:
        SimpleMathOperations operations = new SimpleMathOperations()
    
        when:
        int result = operations.multiply(4, 5)
    
        then:
        assert result == 20
    }


}
