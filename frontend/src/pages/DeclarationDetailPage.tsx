import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Send, CheckCircle } from 'lucide-react';
import { Card, Badge, Button } from '../components/ui';
import { useDeclarationStore } from '../store/declarationStore';

const formTypeLabels: Record<string, string> = {
  'F-07': 'F-07 (IVA)',
  'F-14': 'F-14 (Pago a Cuenta)',
  'F-06': 'F-06 (ISR)',
};

const statusLabels: Record<string, string> = {
  draft: 'Borrador',
  submitted: 'Presentada',
};

const statusBadgeVariant: Record<string, 'warning' | 'success'> = {
  draft: 'warning',
  submitted: 'success',
};

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

function formatCurrency(val: number) {
  return new Intl.NumberFormat('es-SV', { style: 'currency', currency: 'USD' }).format(val);
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('es-SV', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default function DeclarationDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { currentDeclaration, fetchById, submit } = useDeclarationStore();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (id) fetchById(id);
  }, [id, fetchById]);

  if (!currentDeclaration) {
    return (
      <div className="flex items-center justify-center min-h-[40vh]">
        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const decl = currentDeclaration;
  const fields = formFieldLabels[decl.form_type] ?? {};

  const handleSubmit = async () => {
    if (!window.confirm('¿Presentar esta declaración? Esta acción no se puede deshacer.')) return;
    setSubmitting(true);
    setError(null);
    try {
      await submit(decl.declaration_id);
    } catch {
      setError('Error al presentar la declaración');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center space-x-4">
        <button onClick={() => navigate('/declaraciones')} className="p-1 text-gray-500 hover:text-gray-700">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-gray-900">
            {formTypeLabels[decl.form_type] ?? decl.form_type}
          </h1>
          <p className="text-sm text-gray-500">
            Período {decl.period}/{decl.year} · Creado {formatDate(decl.created_at)}
          </p>
        </div>
        <Badge variant={statusBadgeVariant[decl.status]}>
          {statusLabels[decl.status] ?? decl.status}
        </Badge>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          {error}
        </div>
      )}

      <Card title="Datos de la declaración">
        <div className="space-y-3">
          {Object.entries(fields).map(([key, label]) => {
            const val = (decl as any)[key];
            if (val == null) return null;
            return (
              <div key={key} className="flex justify-between items-center py-2 border-b border-gray-100 last:border-0">
                <span className="text-sm font-medium text-gray-600">{label}</span>
                <span className="text-sm font-semibold text-gray-900">
                  {key === 'total_empleados' ? val : formatCurrency(val)}
                </span>
              </div>
            );
          })}
        </div>
      </Card>

      {decl.status === 'draft' && (
        <div className="flex justify-center">
          <Button size="lg" onClick={handleSubmit} loading={submitting}>
            <Send className="w-4 h-4 mr-2" />
            Presentar declaración
          </Button>
        </div>
      )}

      {decl.status === 'submitted' && (
        <Card>
          <div className="flex items-center justify-center space-x-2 text-green-600 py-2">
            <CheckCircle className="w-5 h-5" />
            <span className="font-medium">Ya fue presentada</span>
          </div>
        </Card>
      )}
    </div>
  );
}
