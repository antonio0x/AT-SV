import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('../../lib/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
  },
}));

import api from '../../lib/api';
import { useDeclarationStore } from '../declarationStore';

const mockDeclaration = {
  declaration_id: '1',
  user_id: 'u1',
  form_type: 'F-07',
  period: '01',
  year: 2026,
  status: 'draft',
  total_iva: 150.00,
  created_at: '2026-01-15T00:00:00Z',
};

describe('declarationStore', () => {
  beforeEach(() => {
    useDeclarationStore.setState({
      declarations: [],
      currentDeclaration: null,
      isLoading: false,
      error: null,
      page: 1,
      limit: 50,
      total: 0,
      filters: {},
    });
    vi.clearAllMocks();
  });

  it('fetch loads declarations', async () => {
    (api.get as any).mockResolvedValue({ data: { data: [mockDeclaration], total: 1 } });
    await useDeclarationStore.getState().fetch();
    const state = useDeclarationStore.getState();
    expect(state.declarations).toHaveLength(1);
    expect(state.total).toBe(1);
    expect(api.get).toHaveBeenCalledWith('/declarations', { params: { page: 1, limit: 50 } });
  });

  it('fetch passes filters as params', async () => {
    useDeclarationStore.setState({ filters: { form_type: 'F-07', status: 'draft' } });
    (api.get as any).mockResolvedValue({ data: { data: [], total: 0 } });
    await useDeclarationStore.getState().fetch();
    expect(api.get).toHaveBeenCalledWith('/declarations', {
      params: { page: 1, limit: 50, form_type: 'F-07', status: 'draft' },
    });
  });

  it('fetch sets error on failure', async () => {
    (api.get as any).mockRejectedValue({
      response: { data: { errors: [{ message: 'Server error' }] } },
    });
    await useDeclarationStore.getState().fetch();
    expect(useDeclarationStore.getState().error).toBe('Server error');
  });

  it('fetchById loads a single declaration', async () => {
    (api.get as any).mockResolvedValue({ data: { data: mockDeclaration } });
    await useDeclarationStore.getState().fetchById('1');
    expect(useDeclarationStore.getState().currentDeclaration).toEqual(mockDeclaration);
    expect(api.get).toHaveBeenCalledWith('/declarations/1');
  });

  it('create calls POST and refetches', async () => {
    (api.post as any).mockResolvedValue({ data: { data: mockDeclaration } });
    (api.get as any).mockResolvedValue({ data: { data: [mockDeclaration], total: 1 } });
    const result = await useDeclarationStore.getState().create({ form_type: 'F-07', year: 2026, period: '01' });
    expect(api.post).toHaveBeenCalledWith('/declarations', { form_type: 'F-07', year: 2026, period: '01' });
    expect(result).toEqual(mockDeclaration);
  });

  it('update calls PUT and refetches', async () => {
    (api.put as any).mockResolvedValue({});
    (api.get as any).mockResolvedValue({ data: { data: [], total: 0 } });
    await useDeclarationStore.getState().update('1', { total_iva: 200 });
    expect(api.put).toHaveBeenCalledWith('/declarations/1', { total_iva: 200 });
  });

  it('submit calls POST submit', async () => {
    (api.post as any).mockResolvedValue({});
    (api.get as any).mockResolvedValue({ data: { data: [mockDeclaration], total: 1 } });
    await useDeclarationStore.getState().submit('1');
    expect(api.post).toHaveBeenCalledWith('/declarations/1/submit');
  });

  it('calculate calls POST calculate', async () => {
    (api.post as any).mockResolvedValue({ data: { data: mockDeclaration } });
    const result = await useDeclarationStore.getState().calculate({ form_type: 'F-07', year: 2026, period: '01' });
    expect(api.post).toHaveBeenCalledWith('/declarations/calculate', { form_type: 'F-07', year: 2026, period: '01' });
    expect(result).toEqual(mockDeclaration);
  });

  it('setPage updates page and refetches', async () => {
    (api.get as any).mockResolvedValue({ data: { data: [], total: 0 } });
    await useDeclarationStore.getState().setPage(2);
    expect(useDeclarationStore.getState().page).toBe(2);
    expect(api.get).toHaveBeenCalledWith('/declarations', { params: { page: 2, limit: 50 } });
  });

  it('setFilters resets page to 1 and refetches', async () => {
    useDeclarationStore.setState({ page: 3 });
    (api.get as any).mockResolvedValue({ data: { data: [], total: 0 } });
    await useDeclarationStore.getState().setFilters({ form_type: 'F-14' });
    expect(useDeclarationStore.getState().page).toBe(1);
    expect(useDeclarationStore.getState().filters).toEqual({ form_type: 'F-14' });
  });
});
