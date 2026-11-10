import { useState } from 'react';
import { afterEach, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import user_event from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { CityPicker } from './CityPicker';

const city = {
  id: 3355,
  name: 'Екатеринбург',
  region: 'Свердловская область',
  country: 'RU',
  lat: 56.84,
  lng: 60.61,
  timezone: 'Asia/Yekaterinburg',
};
afterEach(() => vi.unstubAllGlobals());
function render_picker(value: number | null = null, required = false) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const fetch_mock = vi.fn(async (input: RequestInfo | URL) => {
    const path = new URL((input as Request).url);
    return Response.json(
      path.pathname.endsWith('/3355') ? city : { items: [city], total: 1, limit: 20, offset: 0 },
    );
  });
  vi.stubGlobal('fetch', fetch_mock);
  function Field() {
    const [selected, set_selected] = useState(value);
    return <CityPicker value={selected} on_change={set_selected} required={required} />;
  }
  render(
    <QueryClientProvider client={client}>
      <Field />
    </QueryClientProvider>,
  );
  return fetch_mock;
}
it('debounces city suggestions and selects with the keyboard using one input', async () => {
  const fetch_mock = render_picker();
  const user = user_event.setup();
  const field = screen.getByRole('combobox', { name: 'Город' });
  expect(screen.getAllByRole('combobox')).toHaveLength(1);
  await user.type(field, 'Екат');
  await waitFor(() =>
    expect(
      fetch_mock.mock.calls.some(
        ([input]) => new URL((input as Request).url).searchParams.get('q') === 'Екат',
      ),
    ).toBe(true),
  );
  await screen.findByRole('option', { name: /Екатеринбург/ });
  await user.keyboard('{ArrowDown}{Enter}');
  expect(field).toHaveValue('Екатеринбург · Свердловская область');
  expect(field).toHaveAttribute('aria-expanded', 'false');
  await user.click(screen.getByRole('button', { name: 'Очистить город' }));
  expect(field).toHaveValue('');
});
it('restores the selected city by ID and prevents submitting unselected text', async () => {
  render_picker(3355, true);
  const user = user_event.setup();
  const field = screen.getByRole('combobox', { name: 'Город' }) as HTMLInputElement;
  await waitFor(() => expect(field).toHaveValue('Екатеринбург · Свердловская область'));
  expect(field.validity.valid).toBe(true);
  await user.clear(field);
  await user.type(field, 'невыбранный город');
  expect(field.validity.valid).toBe(false);
  await user.keyboard('{Escape}');
  expect(field).toHaveAttribute('aria-expanded', 'false');
});
