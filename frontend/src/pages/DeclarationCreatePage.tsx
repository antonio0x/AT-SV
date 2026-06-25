import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, ArrowRight, Check, Calculator } from 'lucide-react';
import { Button, Input, Select, Card } from '../components/ui';
import { useDeclarationStore, DeclarationBFF } from '../store/declarationStore';

const formTypeOptions = [
  { value: 'F-07', label: 'F-07 (IVA)' },
  { value: 'F-14', label: 'F-14 (Pago a Cuenta)' },
  { value: 'F-06', label: 'F-06 (ISR)' },
];

const months = Array.from({ length: 12 }, (_, i) => ({
  value: String(i + 1).padStart(2, '0'),
  label: String(i + 1).padStart(2, '0'),
}));

type Step = 1 | 2 | 3;

const formFieldLabels: Record<string, Record<string, string>> = {
  'F-07': {
    total_iva: 'Total IVA',
    iva_debito: 'IVA Débito',
    iva_credito: 'IVA Crédito',
    iva_retenido: 'IVA Retenido',
  },
  'F-14': {
    ingresos_brutos: 'Ingresos Brutos',
    tasa_aplicada: 'Tasa Aplicada',
    pago_cuenta_calculado: 'Pago a Cuenta Calculado',
    saldo_a_favor_anterior: 'Saldo a Favor Anterior',
  },
  'F-06': {
    total_remuneraciones: 'Total Remuneraciones',
    total_empleados: 'Total Empleados',
    isr_retenido: 'ISR Retenido',
    cotizaciones_iss: 'Cotizaciones ISS',
    cotizaciones_afp: 'Cotizaciones AFP',
  },
};

export default function DeclarationCreatePage() {
  const navigate = useNavigate();
  const { calculate, create } = useDeclarationStore();

  const [step, setStep] = useState<Step>(1);
  const [formType, setFormType] = useState('F-07');
  const [year, setYear] = useState(String(new Date().getFullYear()));
  const [period, setPeriod] = useState(String(new Date().getMonth() + 1).padStart(2, '0'));
  const [calculated, setCalculated] = useState<DeclarationBFF | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCalculate = async () => {
    setError(null);
    try {
      const result = await calculate({ form_type: formType, year: parseInt(year), period });
      setCalculated(result);
      setStep(2);
    } catch {
      setError('Error al calcular la declaración');
    }
  };

  const handleConfirm = async () => {
    setSubmitting(true);
    setError(null);
    try {
      const decl = await create({
        form_type: formType,
        year: parseInt(year),
        period,
        ...calculated,
      });
      setStep(3);
      setTimeout(() => navigate(`/declaraciones/${decl.declaration_id}`), 1500);
    } catch (err: any) {
      const msg = err.response?.data?.errors?.[0]?.message || 'Error al guardar la declaración';
      setError(msg);
      setSubmitting(false);
    }
  };

  const fields = formFieldLabels[formType] ?? {};

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center space-x-4">
        {step > 1 && (
          <button onClick={() => setStep((step - 1) as Step)} className="p-1 text-gray-500 hover:text-gray-700">
            <ArrowLeft className="w-5 h-5" />
          </button>
        )}
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Nueva declaración</h1>
          <p className="text-sm text-gray-500">
            Paso {step} de 3: {step === 1 ? 'Seleccionar período' : step === 2 ? 'Revisar cálculo' : 'Confirmar'}
          </p>
        </div>
      </div>

      {/* Step indicator */}
      <div className="flex items-center space-x-2">
        {[1, 2, 3].map((s) => (
          <div key={s} className="flex items-center">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                s === step
                  ? 'bg-blue-600 text-white'
                  : s < step
                    ? 'bg-green-500 text-white'
                    : 'bg-gray-200 text-gray-500'
              }`}
            >
              {s < step ? <Check className="w-4 h-4" /> : s}
            </div>
            {s < 3 && <div className={`w-12 h-1 ${s < step ? 'bg-green-500' : 'bg-gray-200'}`} />}
          </div>
        ))}
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          {error}
        </div>
      )}

      {step === 1 && (
        <Card>
          <div className="space-y-4">
            <Select
              label="Tipo de formulario"
              name="form_type"
              value={formType}
              onChange={(e) => setFormType(e.target.value)}
              options={formTypeOptions}
            />
            <div className="grid grid-cols-2 gap-4">
              <Input
                label="Año"
                name="year"
                type="number"
                value={year}
                onChange={(e) => setYear(e.target.value)}
              />
              <Select
                label="Período (mes)"
                name="period"
                value={period}
                onChange={(e) => setPeriod(e.target.value)}
                options={months}
              />
            </div>
            <div className="flex justify-end pt-2">
              <Button onClick={handleCalculate}>
                <Calculator className="w-4 h-4 mr-2" />
                Calcular
              </Button>
            </div>
          </div>
        </Card>
      )}

      {step === 2 && calculated && (
        <Card title="Valores calculados">
          <div className="space-y-4">
            <div className="grid grid-cols-1 gap-4">
              {Object.entries(fields).map(([key, label]) => {
                const val = (calculated as any)[key];
                if (val == null) return null;
                return (
                  <div key={key} className="flex justify-between items-center py-2 border-b border-gray-100 last:border-0">
                    <span className="text-sm font-medium text-gray-600">{label}</span>
                    <span className="text-sm font-semibold text-gray-900">
                      {typeof val === 'number'
                        ? new Intl.NumberFormat('es-SV', { style: 'currency', currency: 'USD' }).format(val)
                        : val}
                    </span>
                  </div>
                );
              })}
            </div>
            <div className="flex justify-end pt-2">
              <Button onClick={handleConfirm} loading={submitting}>
                <Check className="w-4 h-4 mr-2" />
                Guardar como borrador
              </Button>
            </div>
          </div>
        </Card>
      )}

      {step === 3 && (
        <Card>
          <div className="text-center py-8">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Check className="w-8 h-8 text-green-600" />
            </div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">¡Declaración guardada!</h2>
            <p className="text-gray-500">Redirigiendo a los detalles...</p>
          </div>
        </Card>
      )}
    </div>
  );
}
