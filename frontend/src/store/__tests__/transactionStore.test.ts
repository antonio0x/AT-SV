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
import { useTransactionStore } from '../transactionStore';

const mockTx = {
  id: '1',
  user_id: 'u1',
  type: 'income',
  amount: 100,
  category: 'ventas',
  description: 'Test',
  date: '2025-01-15',
  iva_rate: 0.13,
  created_at: '2025-01-15T00:00:00Z',
  updated_at: '2025-01-15T00:00:00Z',
};

describe('transactionStore', () => {
  beforeEach(() => {
    useTransactionStore.setState({
      transactions: [],
      isLoading: false,
      error: null,
      page: 1,
      limit: 50,
      total: 0,
      filters: { type: '' },
    });
    vi.clearAllMocks();
  });

  it('fetchTransactions sets transactions on success', async () => {
    (api.get as any).mockResolvedValue({ data: { data: [mockTx], total: 1 } });
    await useTransactionStore.getState().fetchTransactions();
    const state = useTransactionStore.getState();
    expect(state.transactions).toEqual([mockTx]);
    expect(state.total).toBe(1);
    expect(state.isLoading).toBe(false);
  });

  it('fetchTransactions sets error on failure', async () => {
    (api.get as any).mockRejectedValue({
      response: { data: { errors: [{ message: 'Server error' }] } },
    });
    await useTransactionStore.getState().fetchTransactions();
    const state = useTransactionStore.getState();
    expect(state.error).toBe('Server error');
    expect(state.isLoading).toBe(false);
  });

  it('createTransaction calls POST and re-fetches', async () => {
    (api.post as any).mockResolvedValue({});
    (api.get as any).mockResolvedValue({ data: { data: [mockTx], total: 1 } });
    await useTransactionStore.getState().createTransaction({ type: 'income', amount: 100, category: 'ventas' });
    expect(api.post).toHaveBeenCalledWith('/transactions', {
      type: 'income',
      amount: 100,
      category: 'ventas',
    });
    expect(useTransactionStore.getState().transactions).toEqual([mockTx]);
  });

  it('updateTransaction calls PUT and re-fetches', async () => {
    (api.put as any).mockResolvedValue({});
    (api.get as any).mockResolvedValue({ data: { data: [mockTx], total: 1 } });
    await useTransactionStore.getState().updateTransaction('1', { amount: 200 });
    expect(api.put).toHaveBeenCalledWith('/transactions/1', { amount: 200 });
    expect(useTransactionStore.getState().transactions).toEqual([mockTx]);
  });

  it('deleteTransaction calls DELETE and re-fetches', async () => {
    (api.delete as any).mockResolvedValue({});
    (api.get as any).mockResolvedValue({ data: { data: [], total: 0 } });
    await useTransactionStore.getState().deleteTransaction('1');
    expect(api.delete).toHaveBeenCalledWith('/transactions/1');
    expect(useTransactionStore.getState().transactions).toEqual([]);
  });

  it('setPage updates page and re-fetches', async () => {
    (api.get as any).mockResolvedValue({ data: { data: [], total: 0 } });
    useTransactionStore.getState().setPage(3);
    expect(useTransactionStore.getState().page).toBe(3);
    expect(api.get).toHaveBeenCalled();
  });

  it('setFilters resets to page 1 and re-fetches', async () => {
    useTransactionStore.setState({ page: 5 });
    (api.get as any).mockResolvedValue({ data: { data: [], total: 0 } });
    useTransactionStore.getState().setFilters({ type: 'expense' });
    const state = useTransactionStore.getState();
    expect(state.filters.type).toBe('expense');
    expect(state.page).toBe(1);
  });
});
