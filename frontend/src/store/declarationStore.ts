import { create } from 'zustand';
import api from '../lib/api';

export interface DeclarationBFF {
  declaration_id: string;
  user_id: string;
  form_type: string;
  period: string;
  year: number;
  status: string;
  total_iva?: number | null;
  iva_debito?: number | null;
  iva_credito?: number | null;
  iva_retenido?: number | null;
  ingresos_brutos?: number | null;
  tasa_aplicada?: number | null;
  pago_cuenta_calculado?: number | null;
  saldo_a_favor_anterior?: number | null;
  total_remuneraciones?: number | null;
  total_empleados?: number | null;
  isr_retenido?: number | null;
  cotizaciones_iss?: number | null;
  cotizaciones_afp?: number | null;
  created_at: string;
}

export interface DeclarationFilters {
  form_type?: string;
  year?: string;
  period?: string;
  status?: string;
}

interface DeclarationState {
  declarations: DeclarationBFF[];
  currentDeclaration: DeclarationBFF | null;
  isLoading: boolean;
  error: string | null;
  page: number;
  limit: number;
  total: number;
  filters: DeclarationFilters;
  fetch: () => Promise<void>;
  fetchById: (id: string) => Promise<void>;
  create: (data: Partial<DeclarationBFF>) => Promise<DeclarationBFF>;
  update: (id: string, data: Partial<DeclarationBFF>) => Promise<void>;
  submit: (id: string) => Promise<void>;
  calculate: (data: { form_type: string; year: number; period: string }) => Promise<DeclarationBFF>;
  setPage: (page: number) => void;
  setFilters: (filters: DeclarationFilters) => void;
}

export const useDeclarationStore = create<DeclarationState>((set, get) => ({
  declarations: [],
  currentDeclaration: null,
  isLoading: false,
  error: null,
  page: 1,
  limit: 50,
  total: 0,
  filters: {},

  fetch: async () => {
    set({ isLoading: true, error: null });
    try {
      const { page, limit, filters } = get();
      const params: Record<string, string | number> = { page, limit };
      if (filters.form_type) params.form_type = filters.form_type;
      if (filters.year) params.year = filters.year;
      if (filters.period) params.period = filters.period;
      if (filters.status) params.status = filters.status;
      const res = await api.get('/declarations', { params });
      const body = res.data;
      set({
        declarations: body.data ?? body,
        total: body.total ?? (body.data ?? body).length,
        isLoading: false,
      });
    } catch (err: any) {
      const msg = err.response?.data?.errors?.[0]?.message || 'Error al cargar declaraciones';
      set({ isLoading: false, error: msg });
    }
  },

  fetchById: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      const res = await api.get(`/declarations/${id}`);
      set({ currentDeclaration: res.data.data ?? res.data, isLoading: false });
    } catch (err: any) {
      const msg = err.response?.data?.errors?.[0]?.message || 'Error al cargar declaración';
      set({ isLoading: false, error: msg });
    }
  },

  create: async (data) => {
    set({ isLoading: true, error: null });
    try {
      const res = await api.post('/declarations', data);
      const declaration = res.data.data ?? res.data;
      await get().fetch();
      return declaration;
    } catch (err: any) {
      const msg = err.response?.data?.errors?.[0]?.message || 'Error al crear declaración';
      set({ isLoading: false, error: msg });
      throw err;
    }
  },

  update: async (id, data) => {
    set({ isLoading: true, error: null });
    try {
      await api.put(`/declarations/${id}`, data);
      await get().fetch();
    } catch (err: any) {
      const msg = err.response?.data?.errors?.[0]?.message || 'Error al actualizar declaración';
      set({ isLoading: false, error: msg });
      throw err;
    }
  },

  submit: async (id) => {
    set({ isLoading: true, error: null });
    try {
      await api.post(`/declarations/${id}/submit`);
      await get().fetch();
      await get().fetchById(id);
    } catch (err: any) {
      const msg = err.response?.data?.errors?.[0]?.message || 'Error al presentar declaración';
      set({ isLoading: false, error: msg });
      throw err;
    }
  },

  calculate: async (data) => {
    set({ isLoading: true, error: null });
    try {
      const res = await api.post('/declarations/calculate', data);
      return res.data.data ?? res.data;
    } catch (err: any) {
      const msg = err.response?.data?.errors?.[0]?.message || 'Error al calcular declaración';
      set({ isLoading: false, error: msg });
      throw err;
    }
  },

  setPage: (page) => {
    set({ page });
    get().fetch();
  },

  setFilters: (filters) => {
    set({ filters, page: 1 });
    get().fetch();
  },
}));
