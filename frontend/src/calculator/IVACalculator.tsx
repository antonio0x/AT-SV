import { useState, useCallback } from 'react';
import { IVA_RATE } from '../data/taxRates';

interface IVACalculatorProps {
  onChange: (taxKey: string) => void;
}

function IVACalculator({ onChange }: IVACalculatorProps) {
  const [saleAmount, setSaleAmount] = useState('');
  const [isExempt, setIsExempt] = useState(false);
  const [taxResult, setTaxResult] = useState('0');
  const [totalWithTax, setTotalWithTax] = useState('0');

  const calculateTax = useCallback(() => {
    if (saleAmount === '') return;
    const amount = Number(saleAmount);
    let tax = 0;
    let total = amount;

    if (!isExempt) {
      tax = amount * IVA_RATE;
      total = amount + tax;
    }

    setTaxResult(tax.toFixed(2));
    setTotalWithTax(total.toFixed(2));
    onChange('IVA');
  }, [saleAmount, isExempt, onChange]);

  return (
    <div className="max-w-xl mx-auto p-6 mb-12 bg-white shadow-md rounded-lg border border-gray-100">
      <h2 className="text-xl font-bold mb-6 text-blue-700">Calculadora de IVA</h2>
      <form className="space-y-4" onSubmit={(e) => e.preventDefault()}>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Monto de Venta ($)</label>
          <input
            type="number"
            value={saleAmount}
            onChange={(e) => setSaleAmount(e.target.value)}
            placeholder="Ej: 100"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        <div className="flex items-center space-x-3">
          <input
            type="checkbox"
            id="exempt"
            checked={isExempt}
            onChange={(e) => setIsExempt(e.target.checked)}
            className="w-4 h-4 text-blue-600 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
          />
          <label htmlFor="exempt" className="text-sm text-gray-700">
            Operación Exenta (No aplica IVA)
          </label>
        </div>
        <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-100">
          <div className="p-4 bg-gray-50 rounded-lg text-right">
            <p className="text-sm text-gray-600">IVA (13%)</p>
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
          disabled={saleAmount === ''}
        >
          Calcular IVA
        </button>
      </form>
    </div>
  );
}

export default IVACalculator;
