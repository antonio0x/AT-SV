import { create } from 'zustand';
import api from '../lib/api';

interface UserBFF {
  user_id: string;
  email: string;
  business_name: string;
  business_type: string;
  regimen_fiscal: string;
}

interface RegisterData {
  email: string;
  password: string;
  business_name: string;
  business_type: string;
  nit: string;
  nrc?: string;
  regimen_fiscal: string;
}

interface AuthState {
  user: UserBFF | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  hydrate: () => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,

  hydrate: async () => {
    set({ isLoading: true });
    try {
      const res = await api.get('/users/me');
      set({ user: res.data.data, isAuthenticated: true, isLoading: false });
    } catch {
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },

  login: async (email: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      await api.post('/auth/login', { email, password });
      await get().hydrate();
    } catch (err: any) {
      const msg = err.response?.data?.errors?.[0]?.message || 'Error al iniciar sesión';
      set({ isLoading: false, error: msg });
      throw err;
    }
  },

  register: async (data: RegisterData) => {
    set({ isLoading: true, error: null });
    try {
      await api.post('/auth/register', data);
      await get().hydrate();
    } catch (err: any) {
      const msg = err.response?.data?.errors?.[0]?.message || 'Error al registrarse';
      set({ isLoading: false, error: msg });
      throw err;
    }
  },

  logout: async () => {
    try {
      await api.post('/auth/logout');
    } finally {
      set({ user: null, isAuthenticated: false, error: null });
    }
  },

  clearError: () => set({ error: null }),
}));
