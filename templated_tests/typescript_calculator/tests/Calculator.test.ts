import Calculator from '../src/modules/Calculator';
import { expect } from 'chai';
import 'mocha';
import sinon, { SinonSpy } from 'sinon';

describe('basic', () => {
  it('Can be instantiated', () => {
    const calc = new Calculator();
    expect(calc).is.instanceOf(Calculator);
  });

  it('Displays numbers when they are pressed', () => {
    const calc = new Calculator();
    calc.buttonPressed({
      type: 'number',
      value: '1',
    });
    expect(calc.onDisplay).to.equal('1');

    calc.buttonPressed({
      type: 'number',
      value: '0',
    });

    expect(calc.onDisplay).to.equal('10');

    calc.buttonPressed({
      type: 'number',
      value: '0',
    });

    expect(calc.onDisplay).to.equal('100');
  });

  it('Displays numbers with a decimal when "." is pressed', () => {
    const calc = new Calculator();
    calc.buttonPressed({
      type: 'number',
      value: '1',
    });
    expect(calc.onDisplay).to.equal('1');

    calc.buttonPressed({
      type: 'number',
      value: '0',
    });

    expect(calc.onDisplay).to.equal('10');

    calc.buttonPressed({
      type: 'number',
      value: '0',
    });

    expect(calc.onDisplay).to.equal('100');

    calc.buttonPressed({
      type: 'operator',
      value: '.',
    });

    expect(calc.onDisplay).to.equal('100.');

    calc.buttonPressed({
      type: 'number',
      value: '0',
    });

    expect(calc.onDisplay).to.equal('100.0');

    calc.buttonPressed({
      type: 'number',
      value: '1',
    });

    expect(calc.onDisplay).to.equal('100.01');
  });
});
