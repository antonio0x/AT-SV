import { useState, useCallback } from 'react';
import { ISC_RATES } from '../data/taxRates';

interface ISCCalculatorProps {
  onChange: (taxKey: string) => void;
}

function ISCCalculator({ onChange }: ISCCalculatorProps) {
  const [amount, setAmount] = useState('');
  const [taxType, setTaxType] = useState('tobacco');
  const [taxResult, setTaxResult] = useState('0');
  const [totalWithTax, setTotalWithTax] = useState('0');

  const calculateTax = useCallback(() => {
    if (amount === '') return;
    const base = Number(amount);
    const rate = ISC_RATES[taxType]?.rate ?? 0;
    const tax = base * rate;
    const total = base + tax;

    setTaxResult(tax.toFixed(2));
    setTotalWithTax(total.toFixed(2));
    onChange('ISC');
  }, [amount, taxType, onChange]);

  return (
    <div className="max-w-xl mx-auto p-6 mb-12 bg-white shadow-md rounded-lg border border-gray-100">
      <h2 className="text-xl font-bold mb-6 text-blue-700">Calculadora de ISC</h2>
      <form className="space-y-4" onSubmit={(e) => e.preventDefault()}>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Tipo de Producto</label>
            <select
              value={taxType}
              onChange={(e) => setTaxType(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              {Object.entries(ISC_RATES).map(([key, { name }]) => (
                <option key={key} value={key}>{name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Valor de Venta ($)</label>
            <input
              type="number"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="Ej: 100"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-100">
          <div className="p-4 bg-gray-50 rounded-lg text-right">
            <p className="text-sm text-gray-600">Impuesto Selectivo (ISC)</p>
            <p className="text-xl font-semibold text-gray-900">${taxResult}</p>
          </div>
          <div className="p-4 bg-blue-50 rounded-lg text-right">
            <p className="text-sm text-blue-700">Monto Total</p>
            <p className="text-xl font-bold text-blue-700">${totalWithTax}</p>
          </div>
        </div>
        <button
          type="button"
          className="w-full mt-4 bg-blue-600 text-white px-4 py-3 rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
          onClick={calculateTax}
          disabled={amount === ''}
        >
          Calcular ISC
        </button>
      </form>
    </div>
  );
}

export default ISCCalculator;
