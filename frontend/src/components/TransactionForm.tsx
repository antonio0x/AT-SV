import { useState, useEffect, FormEvent } from 'react';
import { Button, Input, Select } from './ui';
import type { TransactionBFF } from '../store/transactionStore';

const categories = [
  { value: 'ventas', label: 'Ventas' },
  { value: 'servicios', label: 'Servicios' },
  { value: 'servicios_profesionales', label: 'Servicios Profesionales' },
  { value: 'alquileres', label: 'Alquileres' },
  { value: 'honorarios', label: 'Honorarios' },
  { value: 'compras', label: 'Compras' },
  { value: 'otros', label: 'Otros' },
];

interface TransactionFormData {
  type: 'income' | 'expense';
  amount: number;
  category: string;
  description: string;
  date: string;
  iva_rate: number;
}

interface TransactionFormProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: TransactionFormData) => Promise<void>;
  transaction?: TransactionBFF | null;
}

export default function TransactionForm({
  isOpen,
  onClose,
  onSubmit,
  transaction,
}: TransactionFormProps) {
  const [type, setType] = useState<'income' | 'expense'>('income');
  const [amount, setAmount] = useState('');
  const [category, setCategory] = useState('');
  const [description, setDescription] = useState('');
  const [date, setDate] = useState('');
  const [ivaRate, setIvaRate] = useState('0.13');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (transaction) {
      setType(transaction.type);
      setAmount(String(transaction.amount));
      setCategory(transaction.category);
      setDescription(transaction.description ?? '');
      setDate(transaction.date);
      setIvaRate(String(transaction.iva_rate));
    } else {
      setType('income');
      setAmount('');
      setCategory('');
      setDescription('');
      setDate(new Date().toISOString().split('T')[0]);
      setIvaRate('0.13');
    }
    setError(null);
    setSubmitting(false);
  }, [transaction, isOpen]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const numAmount = parseFloat(amount);
    if (isNaN(numAmount) || numAmount <= 0) {
      setError('El monto debe ser un número positivo');
      return;
    }
    if (!category) {
      setError('Seleccione una categoría');
      return;
    }
    const numIva = parseFloat(ivaRate);
    if (isNaN(numIva) || numIva < 0) {
      setError('La tasa de IVA no es válida');
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      await onSubmit({
        type,
        amount: numAmount,
        category,
        description,
        date,
        iva_rate: numIva,
      });
      onClose();
    } catch {
      setError('Error al guardar la transacción');
    } finally {
      setSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />
      <div className="relative bg-white rounded-lg shadow-xl w-full max-w-md mx-4 p-6 z-10">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          {transaction ? 'Editar transacción' : 'Nueva transacción'}
        </h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <Select
            label="Tipo"
            name="type"
            value={type}
            onChange={(e) => setType(e.target.value as 'income' | 'expense')}
            options={[
              { value: 'income', label: 'Ingreso' },
              { value: 'expense', label: 'Gasto' },
            ]}
          />

          <Input
            label="Monto"
            name="amount"
            type="number"
            step="0.01"
            min="0"
            placeholder="0.00"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            required
          />

          <Select
            label="Categoría"
            name="category"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            options={categories}
            placeholder="Seleccione una categoría"
          />

          <Input
            label="Descripción"
            name="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Descripción opcional"
          />

          <Input
            label="Fecha"
            name="date"
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
          />

          <Input
            label="Tasa de IVA"
            name="iva_rate"
            type="number"
            step="0.01"
            min="0"
            max="1"
            value={ivaRate}
            onChange={(e) => setIvaRate(e.target.value)}
          />

          {error && (
            <p className="text-sm text-red-600">{error}</p>
          )}

          <div className="flex justify-end space-x-3 pt-2">
            <Button
              type="button"
              variant="ghost"
              onClick={onClose}
              disabled={submitting}
            >
              Cancelar
            </Button>
            <Button type="submit" loading={submitting}>
              {transaction ? 'Guardar cambios' : 'Crear transacción'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
