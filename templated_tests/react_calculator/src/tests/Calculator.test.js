import React from 'react';
import { shallow } from 'enzyme';
import Calculator from '../modules/Calculator'; 

describe('Calculator Component', () => {
    let wrapper;
    beforeEach(() => {
        wrapper = shallow(<Calculator />);
    });

    test('correctly calculates exponentiation', () => {
        wrapper.instance().handleInput('2');
        wrapper.instance().handleOperation('**');
        wrapper.instance().handleInput('3');
        wrapper.instance().handleEquals();
        expect(wrapper.state('onDisplay')).toBe('8');
    });

    test('correctly calculates modulus', () => {
        wrapper.instance().handleInput('10');
        wrapper.instance().handleOperation('%');
        wrapper.instance().handleInput('3');
        wrapper.instance().handleEquals();
        expect(wrapper.state('onDisplay')).toBe('1');
    });

    test('resets display to 0 on clear', () => {
        wrapper.instance().handleInput('123');
        wrapper.instance().handleClear();
        expect(wrapper.state('onDisplay')).toBe('0');
    });

    test('resets currentTotal to 0 on clear', () => {
        wrapper.instance().handleInput('123');
        wrapper.instance().handleOperation('+');
        wrapper.instance().handleInput('456');
        wrapper.instance().handleEquals();
        wrapper.instance().handleClear();
        expect(wrapper.state('currentTotal')).toBe(0);
    });

    test('resets currentOperator to null on clear', () => {
        wrapper.instance().handleInput('123');
        wrapper.instance().handleOperation('+');
        wrapper.instance().handleClear();
        expect(wrapper.state('currentOperator')).toBeNull();
    });

    test('resets lastActionEquals to false on clear', () => {
        wrapper.instance().handleInput('123');
        wrapper.instance().handleOperation('+');
        wrapper.instance().handleInput('456');
        wrapper.instance().handleEquals();
        wrapper.instance().handleClear();
        expect(wrapper.state('lastActionEquals')).toBe(false);
    });

    test('throws error for invalid operator', () => {
        expect(() => {
            wrapper.instance().evaluate('5', '3', 'invalid_operator');
        }).toThrow("Invalid operator");
    });
});