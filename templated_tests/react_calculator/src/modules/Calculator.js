import React from 'react';
import './Calculator.css';

type OperationFunction = (a: number, b: number) => number;

const operations: { [key: string]: OperationFunction } = {
    "+": (a, b) => a + b,
    "-": (a, b) => a - b,
    "*": (a, b) => a * b,
    "/": (a, b) => a / b,
    "**": (a, b) => a ** b, // Exponentiation
    "%": (a, b) => a % b, // Modulus
};

interface CalculatorState {
    currentTotal: number;
    currentOperator: string | null;
    onDisplay: string;
    lastActionEquals: boolean;
}

class Calculator extends React.Component<{}, CalculatorState> {
    constructor(props: {}) {
        super(props);
        this.state = {
            currentTotal: 0,
            currentOperator: null,
            onDisplay: "0",
            lastActionEquals: false,
        };
    }

    handleInput = (value: string) => {
        this.setState((prevState: CalculatorState) => {
            if (prevState.lastActionEquals) {
                return {
                    onDisplay: value,
                    lastActionEquals: false,
                };
            }
            if (value === '.') {
                if (prevState.onDisplay.includes('.')) {
                    return {};
                }
                if (prevState.onDisplay === '0') {
                    return { onDisplay: '0.' };
                }
            }
            return {
                onDisplay: prevState.onDisplay === "0" ? value : prevState.onDisplay + value,
            };
        });
    };

    handleOperation = (operator: string) => {
        this.setState((prevState: CalculatorState) => ({
            currentTotal: prevState.currentOperator ? this.evaluate(prevState.currentTotal, prevState.onDisplay, prevState.currentOperator) : parseFloat(prevState.onDisplay),
            currentOperator: operator,
            onDisplay: "0",
            lastActionEquals: false,
        }));
    };

    handleClear = () => {
        this.setState({
            currentTotal: 0,
            currentOperator: null,
            onDisplay: "0",
            lastActionEquals: false,
        });
    };

    handleEquals = () => {
        this.setState((prevState: CalculatorState) => ({
            currentTotal: this.evaluate(prevState.currentTotal, prevState.onDisplay, prevState.currentOperator),
            currentOperator: null,
            onDisplay: String(this.evaluate(prevState.currentTotal, prevState.onDisplay, prevState.currentOperator)),
            lastActionEquals: true,
        }));
    };

    evaluate = (left, right, operator) => {
      const leftNum = parseFloat(left);
      const rightNum = parseFloat(right);
      if (!operator || !operations[operator]) {
        throw new Error("Invalid operator");
      }
      const operation = operations[operator];
      return operation(leftNum, rightNum);
    };

    render() {
        return (
            <div className="calculator">
                <div className="display">{this.state.onDisplay}</div>
                <div className="keypad">
                    <button onClick={() => this.handleInput('1')}>1</button>
                    <button onClick={() => this.handleInput('2')}>2</button>
                    <button onClick={() => this.handleInput('3')}>3</button>
                    <button onClick={() => this.handleOperation('+')}>+</button>
                    <button onClick={() => this.handleInput('4')}>4</button>
                    <button onClick={() => this.handleInput('5')}>5</button>
                    <button onClick={() => this.handleInput('6')}>6</button>
                    <button onClick={() => this.handleOperation('-')}>-</button>
                    <button onClick={() => this.handleInput('7')}>7</button>
                    <button onClick={() => this.handleInput('8')}>8</button>
                    <button onClick={() => this.handleInput('9')}>9</button>
                    <button onClick={() => this.handleOperation('*')}>*</button>
                    <button onClick={() => this.handleInput('0')}>0</button>
                    <button onClick={() => this.handleOperation('/')}>/</button>
                    <button onClick={() => this.handleOperation('**')}>^</button>
                    <button onClick={() => this.handleOperation('%')}>%</button>
                    <button onClick={this.handleClear}>C</button>
                    <button onClick={this.handleEquals}>=</button>
                </div>
            </div>
        );
    }
};

export default Calculator;