// Tax rates and brackets for El Salvador (2026)
// Source: Official tax regulations — consult MH for latest updates

interface ISRBracket {
  min: number;
  max: number;
  rate: number;
  label: string;
}

interface ISRRates {
  brackets: ISRBracket[];
  dependentDeduction: number;
}

interface ISCProduct {
  name: string;
  rate: number;
}

interface ISCRates {
  [key: string]: ISCProduct;
}

export const ISR_RATES: ISRRates = {
  brackets: [
    { min: 0, max: 4064.0, rate: 0, label: 'Exento' },
    { min: 4064.01, max: 9142.86, rate: 0.1, label: '10%' },
    { min: 9142.87, max: 22857.14, rate: 0.2, label: '20%' },
    { min: 22857.15, max: Infinity, rate: 0.3, label: '30%' },
  ],
  dependentDeduction: 800,
};

export const IVA_RATE: number = 0.13;

export const ISC_RATES: ISCRates = {
  tobacco: { name: 'Tabaco', rate: 1.0 },
  alcohol: { name: 'Bebidas Alcohólicas', rate: 0.5 },
  softdrinks: { name: 'Bebidas Gaseosas', rate: 0.2 },
  fuels: { name: 'Combustibles', rate: 0.1 },
  others: { name: 'Otros', rate: 0.05 },
};

export const PATRIMONIO_RATE: number = 0.01;
