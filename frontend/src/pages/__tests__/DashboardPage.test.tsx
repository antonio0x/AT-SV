import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import DashboardPage from '../DashboardPage';
import { useAuthStore } from '../../store/authStore';

vi.mock('../../lib/api', () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: { data: { iva_projection: 500, pago_cuenta_projection: 200 } } }),
  },
}));

vi.mock('../../store/declarationStore', () => ({
  useDeclarationStore: vi.fn(() => ({
    declarations: [],
    fetch: vi.fn(),
  })),
}));

function renderPage() {
  return render(
    <MemoryRouter>
      <DashboardPage />
    </MemoryRouter>,
  );
}

describe('DashboardPage', () => {
  beforeEach(() => {
    useAuthStore.setState({ isAuthenticated: true, isLoading: false });
  });

  it('renders title', () => {
    renderPage();
    expect(screen.getByText('Dashboard')).toBeDefined();
  });

  it('renders quick action buttons', () => {
    renderPage();
    expect(screen.getByText('Nueva declaración IVA')).toBeDefined();
    expect(screen.getByText('Nueva declaración Pago a Cuenta')).toBeDefined();
    expect(screen.getByText('Ver transacciones')).toBeDefined();
  });

  it('renders current period', () => {
    renderPage();
    const year = String(new Date().getFullYear());
    expect(screen.getByText(new RegExp(year))).toBeDefined();
  });
});
