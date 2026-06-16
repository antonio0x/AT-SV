import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import TransactionForm from '../TransactionForm';

const defaultProps = {
  isOpen: true,
  onClose: vi.fn(),
  onSubmit: vi.fn().mockResolvedValue(undefined),
  transaction: null,
};

describe('TransactionForm', () => {
  it('renders nothing when closed', () => {
    const { container } = render(
      <TransactionForm {...defaultProps} isOpen={false} />,
    );
    expect(container.innerHTML).toBe('');
  });

  it('renders form fields when open', () => {
    render(<TransactionForm {...defaultProps} />);
    expect(screen.getByLabelText('Tipo')).toBeDefined();
    expect(screen.getByLabelText('Monto')).toBeDefined();
    expect(screen.getByLabelText('Categoría')).toBeDefined();
    expect(screen.getByLabelText('Descripción')).toBeDefined();
    expect(screen.getByLabelText('Fecha')).toBeDefined();
    expect(screen.getByLabelText('Tasa de IVA')).toBeDefined();
  });

  it('shows create title for new transaction', () => {
    render(<TransactionForm {...defaultProps} />);
    expect(screen.getByText('Nueva transacción')).toBeDefined();
  });

  it('shows edit title for existing transaction', () => {
    render(
      <TransactionForm
        {...defaultProps}
        transaction={{
          id: '1',
          user_id: 'u1',
          type: 'expense',
          amount: 500,
          category: 'compras',
          description: 'Office supplies',
          date: '2025-06-01',
          iva_rate: 0.13,
          created_at: '2025-06-01T00:00:00Z',
          updated_at: '2025-06-01T00:00:00Z',
        }}
      />,
    );
    expect(screen.getByText('Editar transacción')).toBeDefined();
  });

  it('pre-fills fields in edit mode', () => {
    render(
      <TransactionForm
        {...defaultProps}
        transaction={{
          id: '1',
          user_id: 'u1',
          type: 'expense',
          amount: 500,
          category: 'compras',
          description: 'Office supplies',
          date: '2025-06-01',
          iva_rate: 0.13,
          created_at: '2025-06-01T00:00:00Z',
          updated_at: '2025-06-01T00:00:00Z',
        }}
      />,
    );
    const montoInput = screen.getByLabelText('Monto') as HTMLInputElement;
    expect(montoInput.value).toBe('500');
    expect(
      (screen.getByLabelText('Descripción') as HTMLInputElement).value,
    ).toBe('Office supplies');
    expect(
      (screen.getByLabelText('Tasa de IVA') as HTMLInputElement).value,
    ).toBe('0.13');
  });

  it('calls onSubmit with form data', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<TransactionForm {...defaultProps} onSubmit={onSubmit} />);
    fireEvent.change(screen.getByLabelText('Monto'), {
      target: { value: '250' },
    });
    fireEvent.change(screen.getByLabelText('Categoría'), {
      target: { value: 'ventas' },
    });
    fireEvent.click(screen.getByText('Crear transacción'));
    await vi.waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          amount: 250,
          category: 'ventas',
          type: 'income',
        }),
      );
    });
  });

  it('calls onClose when cancel is clicked', () => {
    const onClose = vi.fn();
    render(<TransactionForm {...defaultProps} onClose={onClose} />);
    fireEvent.click(screen.getByText('Cancelar'));
    expect(onClose).toHaveBeenCalled();
  });

  it('shows validation error for empty amount', async () => {
    render(<TransactionForm {...defaultProps} />);
    fireEvent.click(screen.getByText('Crear transacción'));
    await vi.waitFor(() => {
      expect(
        screen.getByText('El monto debe ser un número positivo'),
      ).toBeDefined();
    });
  });
});
