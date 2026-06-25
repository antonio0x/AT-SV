import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, act } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import DeclarationDetailPage from '../DeclarationDetailPage';

vi.mock('../../lib/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

let mockDeclaration: any = null;
const mockFetchById = vi.fn();
const mockSubmit = vi.fn();

vi.mock('../../store/declarationStore', () => ({
  useDeclarationStore: vi.fn(() => ({
    currentDeclaration: mockDeclaration,
    fetchById: mockFetchById,
    submit: mockSubmit,
  })),
}));

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/declaraciones/1']}>
      <Routes>
        <Route path="/declaraciones/:id" element={<DeclarationDetailPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

const draftDeclaration = {
  declaration_id: '1',
  user_id: 'u1',
  form_type: 'F-07',
  period: '01',
  year: 2026,
  status: 'draft',
  total_iva: 150.00,
  created_at: '2026-01-15T00:00:00Z',
};

const submittedDeclaration = {
  declaration_id: '2',
  user_id: 'u1',
  form_type: 'F-14',
  period: '02',
  year: 2026,
  status: 'submitted',
  ingresos_brutos: 10000,
  pago_cuenta_calculado: 500,
  created_at: '2026-02-15T00:00:00Z',
};

describe('DeclarationDetailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders declaration details for draft', async () => {
    mockDeclaration = draftDeclaration;
    renderPage();
    expect(screen.getByText('F-07 (IVA)')).toBeDefined();
    expect(screen.getByText('Total IVA')).toBeDefined();
    expect(screen.getByText(/\$150\.00/)).toBeDefined();
  });

  it('shows submit button for draft', () => {
    mockDeclaration = draftDeclaration;
    renderPage();
    expect(screen.getByText('Presentar declaración')).toBeDefined();
  });

  it('shows submitted message for submitted status', () => {
    mockDeclaration = submittedDeclaration;
    renderPage();
    expect(screen.getByText('Ya fue presentada')).toBeDefined();
  });
});
