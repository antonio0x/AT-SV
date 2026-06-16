import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import Button from '../Button';

describe('Button', () => {
  it('renders children', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeDefined();
  });

  it('calls onClick when clicked', () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Click</Button>);
    fireEvent.click(screen.getByText('Click'));
    expect(onClick).toHaveBeenCalledOnce();
  });

  it('shows spinner when loading', () => {
    const { container } = render(<Button loading>Save</Button>);
    expect(container.querySelector('.animate-spin')).toBeDefined();
  });

  it('disables when loading', () => {
    render(<Button loading>Save</Button>);
    expect(screen.getByText('Save')).toBeDisabled();
  });

  it('disables when disabled prop is true', () => {
    render(<Button disabled>Save</Button>);
    expect(screen.getByText('Save')).toBeDisabled();
  });

  it('applies variant classes', () => {
    render(<Button variant="danger">Delete</Button>);
    const btn = screen.getByText('Delete');
    expect(btn.className).toContain('bg-red-600');
  });

  it('applies size classes', () => {
    render(<Button size="lg">Big</Button>);
    expect(screen.getByText('Big').className).toContain('px-6');
  });

  it('applies custom className', () => {
    render(<Button className="my-custom-class">Custom</Button>);
    expect(screen.getByText('Custom').className).toContain('my-custom-class');
  });
});
