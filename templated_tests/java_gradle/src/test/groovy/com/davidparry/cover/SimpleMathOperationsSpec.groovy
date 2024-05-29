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
}
