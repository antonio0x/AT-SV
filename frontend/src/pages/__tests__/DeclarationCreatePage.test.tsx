import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import DeclarationCreatePage from '../DeclarationCreatePage';

vi.mock('../../lib/api', () => ({
  default: {
    post: vi.fn(),
  },
}));

vi.mock('../../store/declarationStore', () => ({
  useDeclarationStore: vi.fn(() => ({
    calculate: vi.fn(),
    create: vi.fn(),
  })),
}));

function renderPage() {
  return render(
    <MemoryRouter>
      <DeclarationCreatePage />
    </MemoryRouter>,
  );
}

describe('DeclarationCreatePage', () => {
  it('renders step 1 with form fields', () => {
    renderPage();
    expect(screen.getByText('Nueva declaración')).toBeDefined();
    expect(screen.getByText('Tipo de formulario')).toBeDefined();
    expect(screen.getByText('Año')).toBeDefined();
    expect(screen.getByText('Período (mes)')).toBeDefined();
    expect(screen.getByText('Calcular')).toBeDefined();
  });

  it('shows step indicator', () => {
    renderPage();
    expect(screen.getByText('1')).toBeDefined();
    expect(screen.getByText('2')).toBeDefined();
    expect(screen.getByText('3')).toBeDefined();
  });
});
