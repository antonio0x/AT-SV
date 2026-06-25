import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('../../lib/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

import api from '../../lib/api';
import { useEmployeeStore } from '../employeeStore';

const mockEmployee = {
  employee_id: '1',
  user_id: 'u1',
  nombre: 'Juan Pérez',
  salario: 1000,
  isr_rate: 0.10,
  iss_deduction: 0.03,
  afp_deduction: 0.0725,
  created_at: '2026-01-15T00:00:00Z',
};

describe('employeeStore', () => {
  beforeEach(() => {
    useEmployeeStore.setState({
      employees: [],
      isLoading: false,
      error: null,
    });
    vi.clearAllMocks();
  });

  it('fetch loads employees', async () => {
    (api.get as any).mockResolvedValue({ data: { data: [mockEmployee] } });
    await useEmployeeStore.getState().fetch();
    expect(useEmployeeStore.getState().employees).toHaveLength(1);
    expect(api.get).toHaveBeenCalledWith('/employees');
  });

  it('fetch sets error on failure', async () => {
    (api.get as any).mockRejectedValue({
      response: { data: { errors: [{ message: 'Server error' }] } },
    });
    await useEmployeeStore.getState().fetch();
    expect(useEmployeeStore.getState().error).toBe('Server error');
  });

  it('create calls POST and refetches', async () => {
    (api.post as any).mockResolvedValue({});
    (api.get as any).mockResolvedValue({ data: { data: [] } });
    await useEmployeeStore.getState().create({ nombre: 'Juan Pérez', salario: 1000 });
    expect(api.post).toHaveBeenCalledWith('/employees', { nombre: 'Juan Pérez', salario: 1000 });
  });

  it('update calls PUT and refetches', async () => {
    (api.put as any).mockResolvedValue({});
    (api.get as any).mockResolvedValue({ data: { data: [] } });
    await useEmployeeStore.getState().update('1', { nombre: 'Pedro López' });
    expect(api.put).toHaveBeenCalledWith('/employees/1', { nombre: 'Pedro López' });
  });

  it('delete calls DELETE and refetches', async () => {
    (api.delete as any).mockResolvedValue({});
    (api.get as any).mockResolvedValue({ data: { data: [] } });
    await useEmployeeStore.getState().delete('1');
    expect(api.delete).toHaveBeenCalledWith('/employees/1');
  });

  it('create sets error on failure', async () => {
    (api.post as any).mockRejectedValue({
      response: { data: { errors: [{ message: 'Failed' }] } },
    });
    await expect(
      useEmployeeStore.getState().create({ nombre: 'Juan', salario: 1000 }),
    ).rejects.toBeDefined();
    expect(useEmployeeStore.getState().error).toBe('Failed');
  });
});
