import { useState, useCallback } from 'react';
import { ISR_RATES } from '../data/taxRates';

interface ISRCalculatorProps {
  onChange: (taxKey: string) => void;
}

function ISRCalculator({ onChange }: ISRCalculatorProps) {
  const [income, setIncome] = useState('');
  const [expenses, setExpenses] = useState('');
  const [dependents, setDependents] = useState(0);
  const [socialContribution, setSocialContribution] = useState('');
  const [taxResult, setTaxResult] = useState('0');

  const calculateTax = useCallback(() => {
    if (income === '' || expenses === '' || socialContribution === '') return;

    const taxableIncome =
      Number(income) -
      Number(expenses) -
      dependents * ISR_RATES.dependentDeduction -
      Number(socialContribution);

    let tax = 0;
    let remaining = taxableIncome;

    for (const bracket of ISR_RATES.brackets) {
      if (remaining <= 0) break;
      const bracketAmount = Math.min(remaining, bracket.max - bracket.min);
      tax += bracketAmount * bracket.rate;
      remaining -= bracketAmount;
    }

    setTaxResult(tax.toFixed(2));
    onChange('ISR');
  }, [income, expenses, dependents, socialContribution, onChange]);

  const hasRequiredFields = income !== '' && expenses !== '' && socialContribution !== '';

  const taxableIncome = hasRequiredFields
    ? Math.max(
        0,
        Number(income) -
          Number(expenses) -
          dependents * ISR_RATES.dependentDeduction -
          Number(socialContribution)
      )
    : 0;

  return (
    <div className="max-w-xl mx-auto p-6 mb-12 bg-white shadow-md rounded-lg border border-gray-100">
      <h2 className="text-xl font-bold mb-6 text-blue-700">Calculadora de ISR</h2>
      <form className="space-y-4" onSubmit={(e) => e.preventDefault()}>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Ingresos Anuales ($)</label>
          <input
            type="number"
            value={income}
            onChange={(e) => setIncome(e.target.value)}
            placeholder="Ej: 20000"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Gastos Deducibles ($)</label>
          <input
            type="number"
            value={expenses}
            onChange={(e) => setExpenses(e.target.value)}
            placeholder="Ej: 5000"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Dependientes</label>
          <input
            type="number"
            value={dependents}
            onChange={(e) => setDependents(e.target.value === '' ? 0 : parseInt(e.target.value) || 0)}
            placeholder="Ej: 2"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            min="0"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Aporte ISSS/AFP ($)</label>
          <input
            type="number"
            value={socialContribution}
            onChange={(e) => setSocialContribution(e.target.value)}
            placeholder="Ej: 1200"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-100">
          <div className="p-4 bg-gray-50 rounded-lg text-right">
            <p className="text-sm text-gray-600">Renta Gravable</p>
            <p className="text-xl font-semibold text-gray-900">${taxableIncome.toFixed(2)}</p>
          </div>
          <div className="p-4 bg-blue-50 rounded-lg text-right">
            <p className="text-sm text-blue-700">Impuesto Calculado</p>
            <p className="text-xl font-bold text-blue-700">${taxResult}</p>
          </div>
        </div>
        <button
          type="button"
          className="w-full mt-4 bg-blue-600 text-white px-4 py-3 rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
          onClick={calculateTax}
          disabled={!hasRequiredFields}
        >
          Calcular ISR
        </button>
      </form>
    </div>
  );
}

export default ISRCalculator;
