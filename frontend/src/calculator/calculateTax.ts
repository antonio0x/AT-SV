// Pure calculation functions — no React, testable directly
import { ISR_RATES, IVA_RATE, ISC_RATES, PATRIMONIO_RATE } from '../data/taxRates';

interface ISRResult {
  taxableIncome: number;
  tax: number;
}

interface IVAResult {
  tax: number;
  total: number;
}

interface ISCResult {
  tax: number;
  total: number;
}

interface PatrimonioResult {
  totalActivos: number;
  patrimonioNeto: number;
  tax: number;
}

interface PatrimonioInputs {
  inmuebles?: number;
  vehiculos?: number;
  activosFinancieros?: number;
  otrosBienes?: number;
  deducciones?: number;
}

export function calculateISR(
  income: number,
  expenses: number,
  dependents: number,
  socialContribution: number
): ISRResult {
  const taxableIncome = Math.max(
    0,
    income - expenses - dependents * ISR_RATES.dependentDeduction - socialContribution
  );

  let tax = 0;
  let remaining = taxableIncome;

  for (const bracket of ISR_RATES.brackets) {
    if (remaining <= 0) break;
    const bracketAmount = Math.min(remaining, bracket.max - bracket.min);
    tax += bracketAmount * bracket.rate;
    remaining -= bracketAmount;
  }

  return { taxableIncome, tax };
}

export function calculateIVA(amount: number, isExempt = false): IVAResult {
  if (isExempt) {
    return { tax: 0, total: amount };
  }
  const tax = amount * IVA_RATE;
  return { tax, total: amount + tax };
}

export function calculateISC(amount: number, productType = 'tobacco'): ISCResult {
  const rate = ISC_RATES[productType]?.rate ?? 0;
  const tax = amount * rate;
  return { tax, total: amount + tax };
}

export function calculatePatrimonio(inputs: PatrimonioInputs = {}): PatrimonioResult {
  const {
    inmuebles = 0,
    vehiculos = 0,
    activosFinancieros = 0,
    otrosBienes = 0,
    deducciones = 0,
  } = inputs;

  const totalActivos = inmuebles + vehiculos + activosFinancieros + otrosBienes;
  const patrimonioNeto = Math.max(0, totalActivos - deducciones);
  const tax = patrimonioNeto * PATRIMONIO_RATE;
  return { totalActivos, patrimonioNeto, tax };
}
