import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import Input from '../Input';

describe('Input', () => {
  it('renders with label', () => {
    render(<Input label="Email" name="email" />);
    expect(screen.getByLabelText('Email')).toBeDefined();
  });

  it('renders without label', () => {
    const { container } = render(<Input name="email" />);
    expect(container.querySelector('input')).toBeDefined();
  });

  it('shows error message', () => {
    render(<Input label="Email" name="email" error="Required field" />);
    expect(screen.getByText('Required field')).toBeDefined();
  });

  it('calls onChange when value changes', () => {
    const onChange = vi.fn();
    render(<Input label="Email" name="email" onChange={onChange} />);
    fireEvent.change(screen.getByLabelText('Email'), {
      target: { value: 'test@test.com' },
    });
    expect(onChange).toHaveBeenCalled();
  });

  it('passes value and placeholder correctly', () => {
    render(
      <Input
        label="Email"
        name="email"
        value="test@test.com"
        onChange={() => {}}
        placeholder="Enter email"
      />,
    );
    const input = screen.getByLabelText('Email') as HTMLInputElement;
    expect(input.value).toBe('test@test.com');
    expect(input.placeholder).toBe('Enter email');
  });

  it('applies custom className', () => {
    const { container } = render(
      <Input name="test" className="extra-class" />,
    );
    expect(container.querySelector('input')?.className).toContain(
      'extra-class',
    );
  });
});
