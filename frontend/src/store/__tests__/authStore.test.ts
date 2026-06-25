import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('../../lib/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

import api from '../../lib/api';
import { useAuthStore } from '../authStore';

describe('authStore', () => {
  beforeEach(() => {
    useAuthStore.setState({ user: null, isAuthenticated: false, isLoading: false, error: null });
    vi.clearAllMocks();
  });

  it('hydrate sets user on 200', async () => {
    const user = { user_id: '1', email: 'a@b.com', business_name: 'Test', business_type: 'persona_natural', regimen_fiscal: 'simplificado' };
    (api.get as any).mockResolvedValue({ data: { data: user } });
    await useAuthStore.getState().hydrate();
    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(true);
    expect(state.user).toEqual(user);
  });

  it('hydrate clears user on 401', async () => {
    (api.get as any).mockRejectedValue({ response: { status: 401 } });
    await useAuthStore.getState().hydrate();
    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(false);
    expect(state.user).toBeNull();
  });

  it('login calls POST and hydrates', async () => {
    (api.post as any).mockResolvedValue({});
    const user = { user_id: '1', email: 'a@b.com', business_name: 'Test', business_type: 'persona_natural', regimen_fiscal: 'simplificado' };
    (api.get as any).mockResolvedValue({ data: { data: user } });
    await useAuthStore.getState().login('a@b.com', 'pass1234');
    expect(api.post).toHaveBeenCalledWith('/auth/login', { email: 'a@b.com', password: 'pass1234' });
    expect(useAuthStore.getState().isAuthenticated).toBe(true);
  });

  it('register calls POST and hydrates', async () => {
    (api.post as any).mockResolvedValue({});
    const user = { user_id: '1', email: 'a@b.com', business_name: 'Test', business_type: 'persona_natural', regimen_fiscal: 'simplificado' };
    (api.get as any).mockResolvedValue({ data: { data: user } });
    const registerData = {
      email: 'a@b.com',
      password: 'pass1234',
      business_name: 'Test',
      business_type: 'persona_natural',
      nit: '0614-290798-101-1',
      regimen_fiscal: 'simplificado',
    };
    await useAuthStore.getState().register(registerData);
    expect(api.post).toHaveBeenCalledWith('/auth/register', registerData);
    expect(useAuthStore.getState().isAuthenticated).toBe(true);
  });

  it('login sets error on failure', async () => {
    (api.post as any).mockRejectedValue({
      response: { data: { errors: [{ message: 'Credenciales inválidas' }] } },
    });
    await expect(useAuthStore.getState().login('a@b.com', 'wrong')).rejects.toBeDefined();
    expect(useAuthStore.getState().error).toBe('Credenciales inválidas');
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
  });

  it('logout clears state', async () => {
    (api.post as any).mockResolvedValue({});
    useAuthStore.setState({ user: { user_id: '1', email: 'a@b.com', business_name: 'Test', business_type: 'persona_natural', regimen_fiscal: 'simplificado' }, isAuthenticated: true });
    await useAuthStore.getState().logout();
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
    expect(useAuthStore.getState().user).toBeNull();
  });

  it('clearError resets error to null', () => {
    useAuthStore.setState({ error: 'something' });
    useAuthStore.getState().clearError();
    expect(useAuthStore.getState().error).toBeNull();
  });
});
