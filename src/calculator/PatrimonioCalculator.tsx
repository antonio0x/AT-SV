import { useState, useCallback } from 'react';
import { PATRIMONIO_RATE } from '../data/taxRates';

interface PatrimonioCalculatorProps {
  onChange: (taxKey: string) => void;
}

function PatrimonioCalculator({ onChange }: PatrimonioCalculatorProps) {
  const [inmuebles, setInmuebles] = useState('');
  const [vehiculos, setVehiculos] = useState('');
  const [activosFinancieros, setActivosFinancieros] = useState('');
  const [otrosBienes, setOtrosBienes] = useState('');
  const [deducciones, setDeducciones] = useState('');
  const [patrimonioResult, setPatrimonioResult] = useState('0');
  const [taxResult, setTaxResult] = useState('0');

  const allFieldsFilled =
    inmuebles !== '' &&
    vehiculos !== '' &&
    activosFinancieros !== '' &&
    otrosBienes !== '' &&
    deducciones !== '';

  const calculateTax = useCallback(() => {
    if (!allFieldsFilled) return;

    const totalActivos =
      Number(inmuebles) +
      Number(vehiculos) +
      Number(activosFinancieros) +
      Number(otrosBienes);
    const patrimonioNeto = Math.max(0, totalActivos - Number(deducciones));
    const impuesto = patrimonioNeto * PATRIMONIO_RATE;

    setPatrimonioResult(totalActivos.toFixed(2));
    setTaxResult(impuesto.toFixed(2));
    onChange('Patrimonio');
  }, [allFieldsFilled, inmuebles, vehiculos, activosFinancieros, otrosBienes, deducciones, onChange]);

  return (
    <div className="max-w-xl mx-auto p-6 mb-12 bg-white shadow-md rounded-lg border border-gray-100">
      <h2 className="text-xl font-bold mb-6 text-blue-700">Calculadora de Impuesto al Patrimonio</h2>
      <form className="space-y-4" onSubmit={(e) => e.preventDefault()}>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Valor de Inmuebles ($)</label>
            <input
              type="number"
              value={inmuebles}
              onChange={(e) => setInmuebles(e.target.value)}
              placeholder="Ej: 200000"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Valor de Vehículos ($)</label>
            <input
              type="number"
              value={vehiculos}
              onChange={(e) => setVehiculos(e.target.value)}
              placeholder="Ej: 50000"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Valores de Inversiones ($)</label>
            <input
              type="number"
              value={activosFinancieros}
              onChange={(e) => setActivosFinancieros(e.target.value)}
              placeholder="Ej: 100000"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Otros Bienes ($)</label>
            <input
              type="number"
              value={otrosBienes}
              onChange={(e) => setOtrosBienes(e.target.value)}
              placeholder="Ej: 15000"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Deducciones ($)
              <span className="text-xs text-gray-500 block mt-1">Ej: Vivienda familiar, contribuciones sociales</span>
            </label>
            <input
              type="number"
              value={deducciones}
              onChange={(e) => setDeducciones(e.target.value)}
              placeholder="Ej: 15000"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-100">
          <div className="p-4 bg-gray-50 rounded-lg text-right">
            <p className="text-sm text-gray-600">Patrimonio Neto</p>
            <p className="text-xl font-semibold text-gray-900">${patrimonioResult}</p>
          </div>
          <div className="p-4 bg-blue-50 rounded-lg text-right">
            <p className="text-sm text-blue-700">Impuesto (1%)</p>
            <p className="text-xl font-bold text-blue-700">${taxResult}</p>
          </div>
        </div>
        <button
          type="button"
          className="w-full mt-4 bg-blue-600 text-white px-4 py-3 rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
          onClick={calculateTax}
          disabled={!allFieldsFilled}
        >
          Calcular Impuesto
        </button>
      </form>
    </div>
  );
}

export default PatrimonioCalculator;
