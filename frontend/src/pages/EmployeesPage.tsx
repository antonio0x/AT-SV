import { useEffect, useState, FormEvent } from 'react';
import { Plus, Pencil, Trash2 } from 'lucide-react';
import { useEmployeeStore, EmployeeBFF } from '../store/employeeStore';
import { Table, Button, Input, Card } from '../components/ui';
import type { Column } from '../components/ui/Table';

function formatCurrency(val: number) {
  return new Intl.NumberFormat('es-SV', { style: 'currency', currency: 'USD' }).format(val);
}

function formatPercent(val: number) {
  return `${(val * 100).toFixed(1)}%`;
}

interface EmployeeFormData {
  nombre: string;
  salario: string;
  isr_rate: string;
  iss_deduction: string;
  afp_deduction: string;
}

const emptyForm: EmployeeFormData = {
  nombre: '',
  salario: '',
  isr_rate: '0.10',
  iss_deduction: '0.03',
  afp_deduction: '0.0725',
};

export default function EmployeesPage() {
  const { employees, isLoading, fetch, create, update, delete: deleteEmployee } = useEmployeeStore();
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<EmployeeBFF | null>(null);
  const [form, setForm] = useState<EmployeeFormData>(emptyForm);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch();
  }, [fetch]);

  const openCreate = () => {
    setEditing(null);
    setForm(emptyForm);
    setError(null);
    setModalOpen(true);
  };

  const openEdit = (emp: EmployeeBFF) => {
    setEditing(emp);
    setForm({
      nombre: emp.nombre,
      salario: String(emp.salario),
      isr_rate: String(emp.isr_rate),
      iss_deduction: String(emp.iss_deduction),
      afp_deduction: String(emp.afp_deduction),
    });
    setError(null);
    setModalOpen(true);
  };

  const handleDelete = async (id: string, nombre: string) => {
    if (window.confirm(`¿Eliminar a "${nombre}"?`)) {
      await deleteEmployee(id);
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const salario = parseFloat(form.salario);
    if (isNaN(salario) || salario <= 0) {
      setError('El salario debe ser un número positivo');
      return;
    }
    if (!form.nombre.trim()) {
      setError('El nombre es obligatorio');
      return;
    }

    setSaving(true);
    setError(null);
    try {
      const data = {
        nombre: form.nombre.trim(),
        salario,
        isr_rate: parseFloat(form.isr_rate),
        iss_deduction: parseFloat(form.iss_deduction),
        afp_deduction: parseFloat(form.afp_deduction),
      };
      if (editing) {
        await update(editing.employee_id, data);
      } else {
        await create(data);
      }
      setModalOpen(false);
    } catch {
      setError('Error al guardar el empleado');
    } finally {
      setSaving(false);
    }
  };

  const columns: Column<EmployeeBFF>[] = [
    { key: 'nombre', label: 'Nombre' },
    {
      key: 'salario',
      label: 'Salario',
      render: (row) => formatCurrency(row.salario),
    },
    {
      key: 'isr_rate',
      label: 'ISR',
      render: (row) => formatPercent(row.isr_rate),
    },
    {
      key: 'iss_deduction',
      label: 'ISS',
      render: (row) => formatPercent(row.iss_deduction),
    },
    {
      key: 'afp_deduction',
      label: 'AFP',
      render: (row) => formatPercent(row.afp_deduction),
    },
    {
      key: 'actions',
      label: 'Acciones',
      render: (row) => (
        <div className="flex space-x-2">
          <button
            onClick={() => openEdit(row)}
            className="p-1.5 rounded-lg text-gray-500 hover:text-blue-600 hover:bg-blue-50 transition-colors"
            title="Editar"
          >
            <Pencil className="w-4 h-4" />
          </button>
          <button
            onClick={() => handleDelete(row.employee_id, row.nombre)}
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
        <h1 className="text-2xl font-bold text-gray-900">Empleados</h1>
        <Button onClick={openCreate}>
          <Plus className="w-4 h-4 mr-2" />
          Nuevo empleado
        </Button>
      </div>

      <Card padding="sm">
        <Table
          columns={columns}
          data={employees}
          loading={isLoading}
          emptyMessage="No hay empleados registrados"
        />
      </Card>

      {/* Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="fixed inset-0 bg-black/50 backdrop-blur-sm"
            onClick={() => setModalOpen(false)}
          />
          <div className="relative bg-white rounded-lg shadow-xl w-full max-w-md mx-4 p-6 z-10">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              {editing ? 'Editar empleado' : 'Nuevo empleado'}
            </h2>

            <form onSubmit={handleSubmit} className="space-y-4">
              <Input
                label="Nombre"
                name="nombre"
                value={form.nombre}
                onChange={(e) => setForm({ ...form, nombre: e.target.value })}
                required
              />
              <Input
                label="Salario"
                name="salario"
                type="number"
                step="0.01"
                min="0"
                value={form.salario}
                onChange={(e) => setForm({ ...form, salario: e.target.value })}
                required
              />
              <div className="grid grid-cols-3 gap-3">
                <Input
                  label="ISR"
                  name="isr_rate"
                  type="number"
                  step="0.001"
                  min="0"
                  max="1"
                  value={form.isr_rate}
                  onChange={(e) => setForm({ ...form, isr_rate: e.target.value })}
                />
                <Input
                  label="ISS"
                  name="iss_deduction"
                  type="number"
                  step="0.001"
                  min="0"
                  max="1"
                  value={form.iss_deduction}
                  onChange={(e) => setForm({ ...form, iss_deduction: e.target.value })}
                />
                <Input
                  label="AFP"
                  name="afp_deduction"
                  type="number"
                  step="0.001"
                  min="0"
                  max="1"
                  value={form.afp_deduction}
                  onChange={(e) => setForm({ ...form, afp_deduction: e.target.value })}
                />
              </div>

              {error && <p className="text-sm text-red-600">{error}</p>}

              <div className="flex justify-end space-x-3 pt-2">
                <Button type="button" variant="ghost" onClick={() => setModalOpen(false)} disabled={saving}>
                  Cancelar
                </Button>
                <Button type="submit" loading={saving}>
                  {editing ? 'Guardar cambios' : 'Crear empleado'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
