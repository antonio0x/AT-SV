import { describe, it, expect } from 'vitest';
import { ISR_RATES, IVA_RATE, ISC_RATES, PATRIMONIO_RATE } from '../../data/taxRates';
import {
  calculateISR,
  calculateIVA,
  calculateISC,
  calculatePatrimonio,
} from '../calculateTax';

// ─── Data Config Tests ───────────────────────────────────────────────

describe('taxRates config', () => {
  it('ISR_RATES has valid bracket structure', () => {
    expect(ISR_RATES.brackets).toHaveLength(4);
    ISR_RATES.brackets.forEach((b) => {
      expect(b).toHaveProperty('min');
      expect(b).toHaveProperty('max');
      expect(b).toHaveProperty('rate');
      expect(b.rate).toBeGreaterThanOrEqual(0);
    });
    expect(ISR_RATES.dependentDeduction).toBe(800);
  });

  it('IVA_RATE is correct', () => {
    expect(IVA_RATE).toBe(0.13);
  });

  it('ISC_RATES has all product types', () => {
    expect(Object.keys(ISC_RATES)).toEqual([
      'tobacco',
      'alcohol',
      'softdrinks',
      'fuels',
      'others',
    ]);
  });

  it('PATRIMONIO_RATE is correct', () => {
    expect(PATRIMONIO_RATE).toBe(0.01);
  });
});

// ─── ISR Tests ────────────────────────────────────────────────────────

describe('calculateISR', () => {
  it('returns 0 tax when income is within exempt bracket', () => {
    const result = calculateISR(3000, 0, 0, 0);
    expect(result.tax).toBe(0);
    expect(result.taxableIncome).toBe(3000);
  });

  it('calculates 10% bracket correctly', () => {
    // Taxable: 5000 → falls in 10% bracket (4064.01 - 9142.86)
    const result = calculateISR(5000, 0, 0, 0);
    expect(result.tax).toBeCloseTo((5000 - 4064) * 0.1, 2);
  });

  it('calculates 20% bracket correctly', () => {
    // Taxable: 15000 → spans 10% and 20%
    const result = calculateISR(15000, 0, 0, 0);
    const bracket1Tax = (9142.86 - 4064.0) * 0.1; // 10% portion
    const bracket2Tax = (15000 - 9142.86) * 0.2; // 20% portion
    expect(result.tax).toBeCloseTo(bracket1Tax + bracket2Tax, 2);
  });

  it('calculates 30% bracket correctly', () => {
    // Taxable: 30000 → spans all brackets
    const result = calculateISR(30000, 0, 0, 0);
    const bracket1Tax = (9142.86 - 4064.0) * 0.1;
    const bracket2Tax = (22857.14 - 9142.86) * 0.2;
    const bracket3Tax = (30000 - 22857.14) * 0.3;
    expect(result.tax).toBeCloseTo(bracket1Tax + bracket2Tax + bracket3Tax, 2);
  });

  it('applies dependent deduction correctly', () => {
    const withoutDependents = calculateISR(20000, 0, 0, 0);
    const withDependents = calculateISR(20000, 0, 2, 0);
    expect(withDependents.taxableIncome).toBeLessThan(withoutDependents.taxableIncome);
    expect(withoutDependents.taxableIncome - withDependents.taxableIncome).toBe(2 * 800);
  });

  it('handles all-zero inputs', () => {
    const result = calculateISR(0, 0, 0, 0);
    expect(result.tax).toBe(0);
    expect(result.taxableIncome).toBe(0);
  });

  it('handles negative taxable income', () => {
    const result = calculateISR(1000, 5000, 0, 0);
    expect(result.tax).toBe(0);
    expect(result.taxableIncome).toBe(0);
  });

  it('applies social contribution deduction', () => {
    const result = calculateISR(20000, 5000, 1, 1200);
    const expectedTaxable = 20000 - 5000 - 800 - 1200;
    expect(result.taxableIncome).toBe(expectedTaxable);
  });
});

// ─── IVA Tests ────────────────────────────────────────────────────────

describe('calculateIVA', () => {
  it('calculates IVA at 13% for non-exempt operations', () => {
    const result = calculateIVA(100, false);
    expect(result.tax).toBe(13);
    expect(result.total).toBe(113);
  });

  it('returns 0 IVA for exempt operations', () => {
    const result = calculateIVA(100, true);
    expect(result.tax).toBe(0);
    expect(result.total).toBe(100);
  });

  it('handles zero amount', () => {
    const result = calculateIVA(0, false);
    expect(result.tax).toBe(0);
    expect(result.total).toBe(0);
  });

  it('defaults to non-exempt', () => {
    const result = calculateIVA(200);
    expect(result.tax).toBe(26);
    expect(result.total).toBe(226);
  });

  it('handles decimal amounts', () => {
    const result = calculateIVA(99.99, false);
    expect(result.tax).toBeCloseTo(13.0, 1);
  });
});

// ─── ISC Tests ────────────────────────────────────────────────────────

describe('calculateISC', () => {
  it('calculates tobacco at 100%', () => {
    const result = calculateISC(100, 'tobacco');
    expect(result.tax).toBe(100);
    expect(result.total).toBe(200);
  });

  it('calculates alcohol at 50%', () => {
    const result = calculateISC(100, 'alcohol');
    expect(result.tax).toBe(50);
    expect(result.total).toBe(150);
  });

  it('calculates soft drinks at 20%', () => {
    const result = calculateISC(100, 'softdrinks');
    expect(result.tax).toBe(20);
    expect(result.total).toBe(120);
  });

  it('calculates fuels at 10%', () => {
    const result = calculateISC(100, 'fuels');
    expect(result.tax).toBe(10);
    expect(result.total).toBe(110);
  });

  it('calculates others at 5%', () => {
    const result = calculateISC(100, 'others');
    expect(result.tax).toBe(5);
    expect(result.total).toBe(105);
  });

  it('defaults to tobacco product type', () => {
    const result = calculateISC(100);
    expect(result.tax).toBe(100);
  });

  it('handles zero amount', () => {
    const result = calculateISC(0, 'tobacco');
    expect(result.tax).toBe(0);
    expect(result.total).toBe(0);
  });

  it('handles unknown product type gracefully', () => {
    const result = calculateISC(100, 'unknown');
    expect(result.tax).toBe(0);
    expect(result.total).toBe(100);
  });
});

// ─── Patrimonio Tests ─────────────────────────────────────────────────

describe('calculatePatrimonio', () => {
  it('calculates 1% tax on net assets', () => {
    const result = calculatePatrimonio({
      inmuebles: 200000,
      vehiculos: 30000,
      activosFinancieros: 50000,
      otrosBienes: 10000,
      deducciones: 40000,
    });
    expect(result.totalActivos).toBe(290000);
    expect(result.patrimonioNeto).toBe(250000);
    expect(result.tax).toBe(2500); // 250000 * 0.01
  });

  it('handles all-zero inputs', () => {
    const result = calculatePatrimonio({
      inmuebles: 0,
      vehiculos: 0,
      activosFinancieros: 0,
      otrosBienes: 0,
      deducciones: 0,
    });
    expect(result.tax).toBe(0);
    expect(result.totalActivos).toBe(0);
  });

  it('uses default values for missing inputs', () => {
    const result = calculatePatrimonio({});
    expect(result.tax).toBe(0);
    expect(result.totalActivos).toBe(0);
  });

  it('handles negative net patrimony', () => {
    const result = calculatePatrimonio({
      inmuebles: 50000,
      vehiculos: 0,
      activosFinancieros: 0,
      otrosBienes: 0,
      deducciones: 100000,
    });
    expect(result.patrimonioNeto).toBe(0);
    expect(result.tax).toBe(0);
  });
});
