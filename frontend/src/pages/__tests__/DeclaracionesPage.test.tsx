import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import DeclaracionesPage from '../DeclaracionesPage';

vi.mock('../../lib/api', () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: { data: [], total: 0 } }),
    post: vi.fn(),
  },
}));

const mockFetch = vi.fn();
vi.mock('../../store/declarationStore', () => ({
  useDeclarationStore: vi.fn(() => ({
    declarations: [],
    isLoading: false,
    page: 1,
    total: 0,
    limit: 50,
    filters: {},
    fetch: mockFetch,
    submit: vi.fn(),
    setPage: vi.fn(),
    setFilters: vi.fn(),
  })),
}));

function renderPage() {
  return render(
    <MemoryRouter>
      <DeclaracionesPage />
    </MemoryRouter>,
  );
}

describe('DeclaracionesPage', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  it('renders title and new button', () => {
    renderPage();
    expect(screen.getByText('Declaraciones')).toBeDefined();
    expect(screen.getByText('Nueva declaración')).toBeDefined();
  });

  it('renders filter controls', () => {
    renderPage();
    expect(screen.getAllByText('Formulario').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('Año').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('Período').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('Estado').length).toBeGreaterThanOrEqual(1);
  });

  it('shows empty message', () => {
    renderPage();
    expect(screen.getByText('No hay declaraciones registradas')).toBeDefined();
  });
});
