import { useState, useCallback } from 'react';
import { Calculator, BarChart3, CheckCircle } from 'lucide-react';
import ISRCalculator from '../calculator/ISRCalculator';
import IVACalculator from '../calculator/IVACalculator';
import ISCCalculator from '../calculator/ISCCalculator';
import PatrimonioCalculator from '../calculator/PatrimonioCalculator';

const tabs = [
  { key: 'ISR', label: 'ISR', description: 'Impuesto sobre la Renta' },
  { key: 'IVA', label: 'IVA', description: 'Impuesto al Valor Agregado' },
  { key: 'ISC', label: 'ISC', description: 'Impuesto Selectivo al Consumo' },
  { key: 'Patrimonio', label: 'Patrimonio', description: 'Impuesto al Patrimonio' },
];

type TabKey = 'ISR' | 'IVA' | 'ISC' | 'Patrimonio';

export default function CalculatorPage() {
  const [selectedTax, setSelectedTax] = useState<TabKey>('ISR');
  const [calculatedTaxes, setCalculatedTaxes] = useState<TabKey[]>([]);

  const handleCalculate = useCallback((taxKey: string) => {
    setCalculatedTaxes((prev) => {
      if (prev.includes(taxKey as TabKey)) return prev;
      return [...prev, taxKey as TabKey];
    });
  }, []);

  const selectedTab = tabs.find((t) => t.key === selectedTax);

  return (
    <div className="w-full min-h-screen bg-gradient-to-br from-gray-50 to-blue-50">
      <div className="safe-area py-16 md:py-24">
        <div className="text-center mb-16">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-600 to-indigo-600 mb-4 mx-auto">
            <Calculator className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-4xl md:text-5xl font-black text-gray-900 mb-4">
            Calculadora de Impuestos
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Calculá de manera precisa tus obligaciones tributarias según la normativa de El Salvador. ISR, IVA, ISC y Patrimonio en un solo lugar.
          </p>
        </div>

        {calculatedTaxes.length > 0 && (
          <div className="mb-8 flex flex-wrap justify-center gap-2">
            {tabs.map((tab) => {
              const isCalculated = calculatedTaxes.includes(tab.key as TabKey);
              return (
                <button
                  key={tab.key}
                  onClick={() => setSelectedTax(tab.key as TabKey)}
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold transition-all ${
                    isCalculated
                      ? 'bg-green-100 text-green-700 hover:bg-green-200'
                      : 'bg-gray-100 text-gray-500'
                  }`}
                >
                  {isCalculated && <CheckCircle className="w-3 h-3" />}
                  {tab.label} {isCalculated ? '✓' : '— pendiente'}
                </button>
              );
            })}
          </div>
        )}

        <div className="mb-12">
          <div className="flex flex-wrap justify-center gap-3">
            {tabs.map((tab) => (
              <button
                key={tab.key}
                type="button"
                onClick={() => setSelectedTax(tab.key as TabKey)}
                className={`group relative px-6 py-3 rounded-xl font-semibold text-sm transition-all duration-200 ${
                  selectedTax === tab.key
                    ? 'bg-gradient-to-br from-blue-600 to-indigo-600 text-white shadow-lg'
                    : 'bg-white text-gray-700 border-2 border-gray-200 hover:border-blue-400 hover:text-blue-600'
                }`}
              >
                {tab.label}
                {selectedTax === tab.key && (
                  <div className="absolute top-full left-1/2 transform -translate-x-1/2 mt-2 px-3 py-1 rounded-lg bg-gray-900 text-white text-xs whitespace-nowrap">
                    {tab.description}
                  </div>
                )}
              </button>
            ))}
          </div>
        </div>

        <div className="relative">
          <div className="absolute -top-10 -right-10 w-40 h-40 bg-blue-200 rounded-full blur-3xl opacity-20 pointer-events-none" />
          <div className="absolute -bottom-10 -left-10 w-40 h-40 bg-indigo-200 rounded-full blur-3xl opacity-20 pointer-events-none" />
          <div className="relative z-10">
            <div className="mb-8 bg-white rounded-2xl p-6 border border-gray-200 shadow-sm">
              <div className="flex items-start space-x-4">
                <div className="w-12 h-12 rounded-lg bg-blue-100 flex items-center justify-center flex-shrink-0">
                  <BarChart3 className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-gray-900">{selectedTab?.label}</h2>
                  <p className="text-gray-600 text-sm mt-1">{selectedTab?.description}</p>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
              {selectedTax === 'ISR' && <ISRCalculator onChange={handleCalculate} />}
              {selectedTax === 'IVA' && <IVACalculator onChange={handleCalculate} />}
              {selectedTax === 'ISC' && <ISCCalculator onChange={handleCalculate} />}
              {selectedTax === 'Patrimonio' && <PatrimonioCalculator onChange={handleCalculate} />}
            </div>
          </div>
        </div>

        <div className="mt-16 grid md:grid-cols-3 gap-6">
          <div className="card">
            <h3 className="font-bold text-gray-900 mb-2">✓ Precisión Garantizada</h3>
            <p className="text-sm text-gray-600">Cálculos 100% precisos según la normativa tributaria actual de El Salvador.</p>
          </div>
          <div className="card">
            <h3 className="font-bold text-gray-900 mb-2">✓ Respuesta Instantánea</h3>
            <p className="text-sm text-gray-600">Obtené resultados inmediatamente. No hay esperas ni complicaciones.</p>
          </div>
          <div className="card">
            <h3 className="font-bold text-gray-900 mb-2">✓ Completamente Gratuito</h3>
            <p className="text-sm text-gray-600">Accedé a todas las calculadoras sin costo. Para siempre.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
