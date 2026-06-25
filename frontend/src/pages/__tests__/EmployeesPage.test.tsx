import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import EmployeesPage from '../EmployeesPage';

vi.mock('../../lib/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

const mockFetch = vi.fn();
vi.mock('../../store/employeeStore', () => ({
  useEmployeeStore: vi.fn(() => ({
    employees: [],
    isLoading: false,
    fetch: mockFetch,
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
  })),
}));

function renderPage() {
  return render(
    <MemoryRouter>
      <EmployeesPage />
    </MemoryRouter>,
  );
}

describe('EmployeesPage', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  it('renders title and new button', () => {
    renderPage();
    expect(screen.getByText('Empleados')).toBeDefined();
    expect(screen.getByText('Nuevo empleado')).toBeDefined();
  });

  it('shows empty message', () => {
    renderPage();
    expect(screen.getByText('No hay empleados registrados')).toBeDefined();
  });

  it('renders table columns', () => {
    renderPage();
    expect(screen.getByText('Nombre')).toBeDefined();
    expect(screen.getByText('Salario')).toBeDefined();
    expect(screen.getByText('ISR')).toBeDefined();
    expect(screen.getByText('ISS')).toBeDefined();
    expect(screen.getByText('AFP')).toBeDefined();
  });
});
