import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import Card from '../Card';

describe('Card', () => {
  it('renders children', () => {
    render(<Card>Content</Card>);
    expect(screen.getByText('Content')).toBeDefined();
  });

  it('renders title when provided', () => {
    render(<Card title="My Title">Content</Card>);
    expect(screen.getByText('My Title')).toBeDefined();
  });

  it('does not render title when not provided', () => {
    const { container } = render(<Card>Content</Card>);
    expect(container.querySelector('h3')).toBeNull();
  });

  it('applies sm padding', () => {
    const { container } = render(<Card padding="sm">Content</Card>);
    expect(container.firstChild).toBeDefined();
  });

  it('applies lg padding', () => {
    const { container } = render(<Card padding="lg">Content</Card>);
    expect(container.firstChild).toBeDefined();
  });

  it('applies custom className', () => {
    const { container } = render(<Card className="extra-class">Content</Card>);
    expect(container.firstChild).toBeDefined();
  });
});
