import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import Select from '../Select';

const options = [
  { value: 'a', label: 'Option A' },
  { value: 'b', label: 'Option B' },
];

describe('Select', () => {
  it('renders with label', () => {
    render(<Select label="Type" name="type" options={options} />);
    expect(screen.getByLabelText('Type')).toBeDefined();
  });

  it('renders all options', () => {
    render(<Select label="Type" name="type" options={options} />);
    expect(screen.getByText('Option A')).toBeDefined();
    expect(screen.getByText('Option B')).toBeDefined();
  });

  it('shows placeholder when provided', () => {
    render(
      <Select
        label="Type"
        name="type"
        options={options}
        placeholder="Select one"
      />,
    );
    expect(screen.getByText('Select one')).toBeDefined();
  });

  it('shows error message', () => {
    render(
      <Select
        label="Type"
        name="type"
        options={options}
        error="Required field"
      />,
    );
    expect(screen.getByText('Required field')).toBeDefined();
  });

  it('calls onChange when selection changes', () => {
    const onChange = vi.fn();
    render(
      <Select label="Type" name="type" options={options} onChange={onChange} />,
    );
    fireEvent.change(screen.getByLabelText('Type'), {
      target: { value: 'b' },
    });
    expect(onChange).toHaveBeenCalled();
  });

  it('sets the selected value', () => {
    render(
      <Select
        label="Type"
        name="type"
        options={options}
        value="a"
        onChange={() => {}}
      />,
    );
    const select = screen.getByLabelText('Type') as HTMLSelectElement;
    expect(select.value).toBe('a');
  });
});
