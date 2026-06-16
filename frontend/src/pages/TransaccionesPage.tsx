import { useEffect, useState, useCallback } from 'react';
import {
  useTransactionStore,
  TransactionBFF,
  TransactionFilters,
} from '../store/transactionStore';
import Table from '../components/ui/Table';
import Badge from '../components/ui/Badge';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import Select from '../components/ui/Select';
import TransactionForm from '../components/TransactionForm';
import { Pencil, Trash2, Plus } from 'lucide-react';

const typeLabels: Record<string, string> = {
  income: 'Ingreso',
  expense: 'Gasto',
};

const typeBadgeVariant: Record<string, 'success' | 'danger'> = {
  income: 'success',
  expense: 'danger',
};

const categoryLabels: Record<string, string> = {
  ventas: 'Ventas',
  servicios: 'Servicios',
  servicios_profesionales: 'Servicios Profesionales',
  alquileres: 'Alquileres',
  honorarios: 'Honorarios',
  compras: 'Compras',
  otros: 'Otros',
};

function formatCurrency(n: number) {
  return new Intl.NumberFormat('es-SV', {
    style: 'currency',
    currency: 'USD',
  }).format(n);
}

function formatDate(iso: string) {
  return new Date(iso + 'T00:00:00').toLocaleDateString('es-SV', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  });
}

export default function TransaccionesPage() {
  const {
    transactions,
    isLoading,
    page,
    limit,
    total,
    filters,
    fetchTransactions,
    deleteTransaction,
    setPage,
    setFilters,
  } = useTransactionStore();

  const [formOpen, setFormOpen] = useState(false);
  const [editingTx, setEditingTx] = useState<TransactionBFF | null>(null);
  const [dateFrom, setDateFrom] = useState(filters.date_from ?? '');
  const [dateTo, setDateTo] = useState(filters.date_to ?? '');
  const [typeFilter, setTypeFilter] = useState(filters.type ?? '');

  useEffect(() => {
    fetchTransactions();
  }, [fetchTransactions]);

  const applyFilters = useCallback(() => {
    const f: TransactionFilters = {};
    if (dateFrom) f.date_from = dateFrom;
    if (dateTo) f.date_to = dateTo;
    if (typeFilter) f.type = typeFilter as 'income' | 'expense';
    setFilters(f);
  }, [dateFrom, dateTo, typeFilter, setFilters]);

  const totalPages = Math.max(1, Math.ceil(total / limit));

  const handleEdit = (tx: TransactionBFF) => {
    setEditingTx(tx);
    setFormOpen(true);
  };

  const handleNew = () => {
    setEditingTx(null);
    setFormOpen(true);
  };

  const handleDelete = async (id: string) => {
    if (window.confirm('¿Eliminar esta transacción?')) {
      await deleteTransaction(id);
    }
  };

  const columns = [
    {
      key: 'date',
      label: 'Fecha',
      render: (row: TransactionBFF) => formatDate(row.date),
    },
    {
      key: 'type',
      label: 'Tipo',
      render: (row: TransactionBFF) => (
        <Badge variant={typeBadgeVariant[row.type]}>
          {typeLabels[row.type]}
        </Badge>
      ),
    },
    {
      key: 'amount',
      label: 'Monto',
      render: (row: TransactionBFF) => (
        <span className={row.type === 'income' ? 'text-green-600' : 'text-red-600'}>
          {row.type === 'income' ? '+' : '-'}{formatCurrency(row.amount)}
        </span>
      ),
    },
    {
      key: 'category',
      label: 'Categoría',
      render: (row: TransactionBFF) => categoryLabels[row.category] ?? row.category,
    },
    {
      key: 'iva_rate',
      label: 'IVA',
      render: (row: TransactionBFF) => `${(row.iva_rate * 100).toFixed(0)}%`,
    },
    {
      key: 'actions',
      label: 'Acciones',
      render: (row: TransactionBFF) => (
        <div className="flex space-x-2">
          <button
            onClick={() => handleEdit(row)}
            className="p-1.5 rounded-lg text-gray-500 hover:text-blue-600 hover:bg-blue-50 transition-colors"
            title="Editar"
          >
            <Pencil className="w-4 h-4" />
          </button>
          <button
            onClick={() => handleDelete(row.id)}
            className="p-1.5 rounded-lg text-gray-500 hover:text-red-600 hover:bg-red-50 transition-colors"
            title="Eliminar"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Transacciones</h1>
        <Button onClick={handleNew}>
          <Plus className="w-4 h-4 mr-2" />
          Nueva transacción
        </Button>
      </div>

      <Card padding="md">
        <div className="flex flex-wrap gap-4 items-end">
          <div className="w-44">
            <Input
              label="Desde"
              name="date_from"
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
            />
          </div>
          <div className="w-44">
            <Input
              label="Hasta"
              name="date_to"
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
            />
          </div>
          <div className="w-44">
            <Select
              label="Tipo"
              name="type_filter"
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              options={[
                { value: '', label: 'Todos' },
                { value: 'income', label: 'Ingreso' },
                { value: 'expense', label: 'Gasto' },
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
          data={transactions}
          loading={isLoading}
          emptyMessage="No hay transacciones registradas"
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

      <TransactionForm
        isOpen={formOpen}
        onClose={() => {
          setFormOpen(false);
          setEditingTx(null);
        }}
        transaction={editingTx}
        onSubmit={async (data) => {
          const store = useTransactionStore.getState();
          if (editingTx) {
            await store.updateTransaction(editingTx.id, data);
          } else {
            await store.createTransaction(data);
          }
        }}
      />
    </div>
  );
}
