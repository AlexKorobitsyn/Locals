import { expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import user_event from '@testing-library/user-event';
import { useState } from 'react';
import { Select } from './Select';

function Form({ submit }: { submit: () => void }) {
  const [value, set_value] = useState('');
  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        submit();
      }}
    >
      <label>
        Город
        <Select label="Город" value={value} on_change={set_value} required>
          <option value="">Выберите город</option>
          <option value="1">Москва</option>
          <option value="2" disabled>
            Недоступный город
          </option>
          <option value="3">Тверь</option>
        </Select>
      </label>
      <button type="submit">Сохранить</button>
    </form>
  );
}

it('opens on one click, chooses an option, closes outside and reopens', async () => {
  render(<Form submit={vi.fn()} />);
  const user = user_event.setup();
  const picker = screen.getByRole('combobox', { name: 'Город' });
  await user.click(picker);
  expect(picker).toHaveAttribute('aria-expanded', 'true');
  await user.click(screen.getByRole('option', { name: 'Москва' }));
  expect(picker).toHaveTextContent('Москва');
  expect(picker).toHaveFocus();
  expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
  await user.click(picker);
  await user.click(document.body);
  expect(picker).toHaveAttribute('aria-expanded', 'false');
  await user.click(picker);
  expect(screen.getByRole('listbox')).toBeInTheDocument();
});

it('supports keyboard selection, skips disabled entries and cancels with Escape', async () => {
  render(<Form submit={vi.fn()} />);
  const user = user_event.setup();
  const picker = screen.getByRole('combobox', { name: 'Город' });
  await user.tab();
  await user.keyboard('{ArrowDown}{ArrowDown}{Enter}');
  expect(picker).toHaveTextContent('Тверь');
  await user.keyboard('{Home}{Escape}');
  expect(picker).toHaveTextContent('Тверь');
  expect(picker).toHaveAttribute('aria-expanded', 'false');
  await user.keyboard('М{Enter}');
  expect(picker).toHaveTextContent('Москва');
});

it('blocks form submission until a required option is selected', async () => {
  const submit = vi.fn();
  render(<Form submit={submit} />);
  const user = user_event.setup();
  await user.click(screen.getByRole('button', { name: 'Сохранить' }));
  expect(submit).not.toHaveBeenCalled();
  expect(screen.getByRole('combobox', { name: 'Город' })).toHaveAttribute('aria-invalid', 'true');
  await user.click(screen.getByRole('combobox', { name: 'Город' }));
  await user.click(screen.getByRole('option', { name: 'Тверь' }));
  await user.click(screen.getByRole('button', { name: 'Сохранить' }));
  expect(submit).toHaveBeenCalledOnce();
});
