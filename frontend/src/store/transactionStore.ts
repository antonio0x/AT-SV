import { create } from 'zustand';
import api from '../lib/api';

export interface TransactionBFF {
  id: string;
  user_id: string;
  type: 'income' | 'expense';
  amount: number;
  category: string;
  description: string | null;
  date: string;
  iva_rate: number;
  created_at: string;
  updated_at: string;
}

export interface TransactionFilters {
  date_from?: string;
  date_to?: string;
  type?: 'income' | 'expense' | '';
}

interface TransactionState {
  transactions: TransactionBFF[];
  isLoading: boolean;
  error: string | null;
  page: number;
  limit: number;
  total: number;
  filters: TransactionFilters;
  fetchTransactions: () => Promise<void>;
  createTransaction: (data: Partial<TransactionBFF>) => Promise<void>;
  updateTransaction: (id: string, data: Partial<TransactionBFF>) => Promise<void>;
  deleteTransaction: (id: string) => Promise<void>;
  setPage: (page: number) => void;
  setFilters: (filters: TransactionFilters) => void;
}

export const useTransactionStore = create<TransactionState>((set, get) => ({
  transactions: [],
  isLoading: false,
  error: null,
  page: 1,
  limit: 50,
  total: 0,
  filters: { type: '' },

  fetchTransactions: async () => {
    set({ isLoading: true, error: null });
    try {
      const { page, limit, filters } = get();
      const params: Record<string, string | number> = { page, limit };
      if (filters.date_from) params.date_from = filters.date_from;
      if (filters.date_to) params.date_to = filters.date_to;
      if (filters.type) params.type = filters.type;
      const res = await api.get('/transactions', { params });
      const body = res.data;
      set({
        transactions: body.data ?? body,
        total: body.total ?? (body.data ?? body).length,
        isLoading: false,
      });
    } catch (err: any) {
      const msg = err.response?.data?.errors?.[0]?.message || 'Error al cargar transacciones';
      set({ isLoading: false, error: msg });
    }
  },

  createTransaction: async (data) => {
    set({ isLoading: true, error: null });
    try {
      await api.post('/transactions', data);
      await get().fetchTransactions();
    } catch (err: any) {
      const msg = err.response?.data?.errors?.[0]?.message || 'Error al crear transacción';
      set({ isLoading: false, error: msg });
      throw err;
    }
  },

  updateTransaction: async (id, data) => {
    set({ isLoading: true, error: null });
    try {
      await api.put(`/transactions/${id}`, data);
      await get().fetchTransactions();
    } catch (err: any) {
      const msg = err.response?.data?.errors?.[0]?.message || 'Error al actualizar transacción';
      set({ isLoading: false, error: msg });
      throw err;
    }
  },

  deleteTransaction: async (id) => {
    set({ isLoading: true, error: null });
    try {
      await api.delete(`/transactions/${id}`);
      await get().fetchTransactions();
    } catch (err: any) {
      const msg = err.response?.data?.errors?.[0]?.message || 'Error al eliminar transacción';
      set({ isLoading: false, error: msg });
      throw err;
    }
  },

  setPage: (page) => {
    set({ page });
    get().fetchTransactions();
  },

  setFilters: (filters) => {
    set({ filters, page: 1 });
    get().fetchTransactions();
  },
}));
