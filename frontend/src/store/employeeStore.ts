import { create } from 'zustand';
import api from '../lib/api';

export interface EmployeeBFF {
  employee_id: string;
  user_id: string;
  nombre: string;
  salario: number;
  isr_rate: number;
  iss_deduction: number;
  afp_deduction: number;
  created_at: string;
}

interface EmployeeState {
  employees: EmployeeBFF[];
  isLoading: boolean;
  error: string | null;
  fetch: () => Promise<void>;
  create: (data: Partial<EmployeeBFF>) => Promise<void>;
  update: (id: string, data: Partial<EmployeeBFF>) => Promise<void>;
  delete: (id: string) => Promise<void>;
}

export const useEmployeeStore = create<EmployeeState>((set, get) => ({
  employees: [],
  isLoading: false,
  error: null,

  fetch: async () => {
    set({ isLoading: true, error: null });
    try {
      const res = await api.get('/employees');
      const body = res.data;
      set({ employees: body.data ?? body, isLoading: false });
    } catch (err: any) {
      const msg = err.response?.data?.errors?.[0]?.message || 'Error al cargar empleados';
      set({ isLoading: false, error: msg });
    }
  },

  create: async (data) => {
    set({ isLoading: true, error: null });
    try {
      await api.post('/employees', data);
      await get().fetch();
    } catch (err: any) {
      const msg = err.response?.data?.errors?.[0]?.message || 'Error al crear empleado';
      set({ isLoading: false, error: msg });
      throw err;
    }
  },

  update: async (id, data) => {
    set({ isLoading: true, error: null });
    try {
      await api.put(`/employees/${id}`, data);
      await get().fetch();
    } catch (err: any) {
      const msg = err.response?.data?.errors?.[0]?.message || 'Error al actualizar empleado';
      set({ isLoading: false, error: msg });
      throw err;
    }
  },

  delete: async (id) => {
    set({ isLoading: true, error: null });
    try {
      await api.delete(`/employees/${id}`);
      await get().fetch();
    } catch (err: any) {
      const msg = err.response?.data?.errors?.[0]?.message || 'Error al eliminar empleado';
      set({ isLoading: false, error: msg });
      throw err;
    }
  },
}));
