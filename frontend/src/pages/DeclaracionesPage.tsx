import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Eye, Pencil, Send } from 'lucide-react';
import { useDeclarationStore, DeclarationBFF, DeclarationFilters } from '../store/declarationStore';
import { Table, Badge, Button, Card, Select, Input } from '../components/ui';
import type { Column } from '../components/ui/Table';

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

const months = Array.from({ length: 12 }, (_, i) => ({
  value: String(i + 1).padStart(2, '0'),
  label: String(i + 1).padStart(2, '0'),
}));

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('es-SV', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  });
}

export default function DeclaracionesPage() {
  const navigate = useNavigate();
  const {
    declarations,
    isLoading,
    page,
    total,
    limit,
    filters,
    fetch,
    submit,
    setPage,
    setFilters,
  } = useDeclarationStore();

  const [formType, setFormType] = useState(filters.form_type ?? '');
  const [year, setYear] = useState(filters.year ?? '');
  const [period, setPeriod] = useState(filters.period ?? '');
  const [status, setStatus] = useState(filters.status ?? '');

  useEffect(() => {
    fetch();
  }, [fetch]);

  const applyFilters = useCallback(() => {
    const f: DeclarationFilters = {};
    if (formType) f.form_type = formType;
    if (year) f.year = year;
    if (period) f.period = period;
    if (status) f.status = status;
    setFilters(f);
  }, [formType, year, period, status, setFilters]);

  const totalPages = Math.max(1, Math.ceil(total / limit));

  const handleSubmit = async (id: string) => {
    if (window.confirm('¿Presentar esta declaración?')) {
      await submit(id);
    }
  };

  const columns: Column<DeclarationBFF>[] = [
    {
      key: 'form_type',
      label: 'Formulario',
      render: (row) => formTypeLabels[row.form_type] ?? row.form_type,
    },
    {
      key: 'period',
      label: 'Período',
      render: (row) => row.period,
    },
    {
      key: 'year',
      label: 'Año',
      render: (row) => String(row.year),
    },
    {
      key: 'status',
      label: 'Estado',
      render: (row) => (
        <Badge variant={statusBadgeVariant[row.status]}>
          {statusLabels[row.status] ?? row.status}
        </Badge>
      ),
    },
    {
      key: 'created_at',
      label: 'Creado',
      render: (row) => formatDate(row.created_at),
    },
    {
      key: 'actions',
      label: 'Acciones',
      render: (row) => (
        <div className="flex space-x-2">
          <button
            onClick={() => navigate(`/declaraciones/${row.declaration_id}`)}
            className="p-1.5 rounded-lg text-gray-500 hover:text-blue-600 hover:bg-blue-50 transition-colors"
            title="Ver"
          >
            <Eye className="w-4 h-4" />
          </button>
          {row.status === 'draft' && (
            <>
              <button
                onClick={() => navigate(`/declaraciones/${row.declaration_id}`)}
                className="p-1.5 rounded-lg text-gray-500 hover:text-amber-600 hover:bg-amber-50 transition-colors"
                title="Editar"
              >
                <Pencil className="w-4 h-4" />
              </button>
              <button
                onClick={() => handleSubmit(row.declaration_id)}
                className="p-1.5 rounded-lg text-gray-500 hover:text-green-600 hover:bg-green-50 transition-colors"
                title="Presentar"
              >
                <Send className="w-4 h-4" />
              </button>
            </>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Declaraciones</h1>
        <Button onClick={() => navigate('/declaraciones/nueva')}>
          <Plus className="w-4 h-4 mr-2" />
          Nueva declaración
        </Button>
      </div>

      <Card padding="md">
        <div className="flex flex-wrap gap-4 items-end">
          <div className="w-44">
            <Select
              label="Formulario"
              name="form_type"
              value={formType}
              onChange={(e) => setFormType(e.target.value)}
              options={[
                { value: '', label: 'Todos' },
                { value: 'F-07', label: 'F-07 (IVA)' },
                { value: 'F-14', label: 'F-14 (Pago a Cuenta)' },
                { value: 'F-06', label: 'F-06 (ISR)' },
              ]}
            />
          </div>
          <div className="w-32">
            <Input
              label="Año"
              name="year"
              type="number"
              placeholder="2026"
              value={year}
              onChange={(e) => setYear(e.target.value)}
            />
          </div>
          <div className="w-32">
            <Select
              label="Período"
              name="period"
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
              options={[{ value: '', label: 'Todos' }, ...months]}
            />
          </div>
          <div className="w-44">
            <Select
              label="Estado"
              name="status"
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              options={[
                { value: '', label: 'Todos' },
                { value: 'draft', label: 'Borrador' },
                { value: 'submitted', label: 'Presentada' },
              ]}
            />
          </div>
          <div>
            <Button variant="secondary" onClick={applyFilters}>
              Filtrar
            </Button>
          </div>
        </div>
      </Card>

      <Card padding="sm">
        <Table
          columns={columns}
          data={declarations}
          loading={isLoading}
          emptyMessage="No hay declaraciones registradas"
        />
      </Card>

      {totalPages > 1 && (
        <div className="flex items-center justify-center space-x-4">
          <Button
            variant="ghost"
            disabled={page <= 1}
            onClick={() => setPage(page - 1)}
          >
            Anterior
          </Button>
          <span className="text-sm text-gray-600">
            Página {page} de {totalPages}
          </span>
          <Button
            variant="ghost"
            disabled={page >= totalPages}
            onClick={() => setPage(page + 1)}
          >
            Siguiente
          </Button>
        </div>
      )}
    </div>
  );
}
