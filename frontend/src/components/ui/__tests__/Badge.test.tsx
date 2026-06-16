import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import Badge from '../Badge';

describe('Badge', () => {
  it('renders children', () => {
    render(<Badge>Active</Badge>);
    expect(screen.getByText('Active')).toBeDefined();
  });

  it('applies primary variant by default', () => {
    render(<Badge>Default</Badge>);
    expect(screen.getByText('Default').className).toContain('bg-blue-100');
  });

  it('applies success variant', () => {
    render(<Badge variant="success">Success</Badge>);
    expect(screen.getByText('Success').className).toContain('bg-green-100');
  });

  it('applies warning variant', () => {
    render(<Badge variant="warning">Warning</Badge>);
    expect(screen.getByText('Warning').className).toContain('bg-yellow-100');
  });

  it('applies danger variant', () => {
    render(<Badge variant="danger">Danger</Badge>);
    expect(screen.getByText('Danger').className).toContain('bg-red-100');
  });

  it('applies info variant', () => {
    render(<Badge variant="info">Info</Badge>);
    expect(screen.getByText('Info').className).toContain('bg-gray-100');
  });
});
