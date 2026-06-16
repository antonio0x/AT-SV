import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import TransaccionesPage from '../TransaccionesPage';
import { useTransactionStore } from '../../store/transactionStore';

vi.mock('../../lib/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

const mockTx = {
  id: '1',
  user_id: 'u1',
  type: 'income' as const,
  amount: 1000,
  category: 'ventas',
  description: 'Sale',
  date: '2025-06-15',
  iva_rate: 0.13,
  created_at: '2025-06-15T00:00:00Z',
  updated_at: '2025-06-15T00:00:00Z',
};

function renderPage() {
  return render(
    <MemoryRouter>
      <TransaccionesPage />
    </MemoryRouter>,
  );
}

describe('TransaccionesPage', () => {
  beforeEach(() => {
    useTransactionStore.setState({
      transactions: [mockTx],
      isLoading: false,
      error: null,
      page: 1,
      limit: 50,
      total: 1,
      filters: { type: '' },
    });
  });

  it('renders page title', () => {
    renderPage();
    expect(screen.getByText('Transacciones')).toBeDefined();
  });

  it('renders new transaction button', () => {
    renderPage();
    expect(screen.getByText('Nueva transacción')).toBeDefined();
  });

  it('renders transaction data in table', () => {
    renderPage();
    expect(screen.getByText('$1,000.00')).toBeDefined();
    expect(screen.getByText('Ventas')).toBeDefined();
    expect(screen.getByText('Ingreso')).toBeDefined();
    expect(screen.getByText('13%')).toBeDefined();
  });

  it('renders filter inputs', () => {
    renderPage();
    expect(screen.getByLabelText('Desde')).toBeDefined();
    expect(screen.getByLabelText('Hasta')).toBeDefined();
    expect(screen.getByText('Filtrar')).toBeDefined();
  });

  it('shows empty message when no transactions', () => {
    useTransactionStore.setState({ transactions: [], total: 0 });
    renderPage();
    expect(screen.getByText('No hay transacciones registradas')).toBeDefined();
  });

  it('shows loading state', () => {
    useTransactionStore.setState({ isLoading: true, transactions: [] });
    const { container } = renderPage();
    expect(container.querySelector('.animate-pulse')).toBeDefined();
  });

  it('opens form when clicking Nueva transacción', () => {
    renderPage();
    fireEvent.click(screen.getByText('Nueva transacción'));
    expect(screen.getByText('Nueva transacción')).toBeDefined();
  });

  it('shows category label for income type', () => {
    renderPage();
    expect(screen.getByText('Ingreso')).toBeDefined();
  });
});
