import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import Table from '../Table';

interface TestItem {
  id: number;
  name: string;
  value: string;
}

const columns = [
  { key: 'name', label: 'Name' },
  { key: 'value', label: 'Value' },
];

const data: TestItem[] = [
  { id: 1, name: 'Alpha', value: '100' },
  { id: 2, name: 'Beta', value: '200' },
];

describe('Table', () => {
  it('renders column headers', () => {
    render(<Table columns={columns} data={[]} />);
    expect(screen.getByText('Name')).toBeDefined();
    expect(screen.getByText('Value')).toBeDefined();
  });

  it('renders data rows', () => {
    render(<Table columns={columns} data={data} />);
    expect(screen.getByText('Alpha')).toBeDefined();
    expect(screen.getByText('Beta')).toBeDefined();
  });

  it('shows skeleton rows when loading', () => {
    const { container } = render(<Table columns={columns} data={[]} loading />);
    expect(container.querySelector('.animate-pulse')).toBeDefined();
  });

  it('shows empty message when no data', () => {
    render(<Table columns={columns} data={[]} emptyMessage="Nothing here" />);
    expect(screen.getByText('Nothing here')).toBeDefined();
  });

  it('renders custom render function', () => {
    const cols = [
      { key: 'name', label: 'Name' },
      {
        key: 'actions',
        label: 'Actions',
        render: (item: TestItem) => <button>Edit {item.name}</button>,
      },
    ];
    render(<Table columns={cols} data={data} />);
    expect(screen.getByText('Edit Alpha')).toBeDefined();
    expect(screen.getByText('Edit Beta')).toBeDefined();
  });

  it('uses row id as key when available', () => {
    const { container } = render(<Table columns={columns} data={data} />);
    expect(container.querySelector('tbody')).toBeDefined();
  });
});
