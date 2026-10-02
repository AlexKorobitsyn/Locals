import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import user_event from '@testing-library/user-event';
import { QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router';
import { query_client } from '../../app/query';
import { RatingControl } from './RatingControl';

vi.mock('../auth/AuthProvider', () => ({ use_auth: () => ({ user: { id: 1 } }) }));
beforeEach(() => query_client.clear());
afterEach(() => {
  query_client.clear();
  vi.unstubAllGlobals();
});
function render_rating(my_rating: number | null = null) {
  render(
    <QueryClientProvider client={query_client}>
      <MemoryRouter>
        <RatingControl target_type="track" target_id={42} my_rating={my_rating} />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

it('sends a numeric half-step and invalidates catalog, recommendations and reviews', async () => {
  const fetch_mock = vi.fn(async (_input: RequestInfo | URL) =>
    Response.json({
      target_type: 'track',
      target_id: 42,
      my_rating: 4.5,
      rating_avg: 3.02,
      ratings_count: 1,
    }),
  );
  vi.stubGlobal('fetch', fetch_mock);
  for (const key of ['catalog', 'recommendations', 'reviews'])
    query_client.setQueryData([key, 1], {});
  render_rating();
  const user = user_event.setup();
  await user.click(screen.getByRole('radio', { name: '4.5 из 5' }));
  await user.click(screen.getByRole('button', { name: 'Оценить' }));
  await screen.findByRole('status');
  const request = fetch_mock.mock.calls[0]?.[0] as Request;
  expect(await request.json()).toEqual({ target_type: 'track', target_id: 42, value: 4.5 });
  for (const key of ['catalog', 'recommendations', 'reviews'])
    expect(query_client.getQueryState([key, 1])?.isInvalidated).toBe(true);
});

it('requires confirmation before deleting the rating and review', async () => {
  const fetch_mock = vi.fn(async (_input: RequestInfo | URL) => Response.json({ my_rating: null }));
  vi.stubGlobal('fetch', fetch_mock);
  render_rating(4.5);
  const user = user_event.setup();
  await user.click(screen.getByRole('button', { name: 'Удалить оценку' }));
  expect(fetch_mock).not.toHaveBeenCalled();
  expect(screen.getByRole('alertdialog')).toHaveTextContent('также удалит вашу рецензию');
  await user.click(screen.getByRole('button', { name: 'Удалить оценку и рецензию' }));
  await waitFor(() => expect(fetch_mock).toHaveBeenCalledOnce());
  const request = fetch_mock.mock.calls[0]?.[0] as Request;
  expect(request.method).toBe('DELETE');
  expect(request.url).toContain('/ratings/track/42');
});

it('chooses half-stars by keyboard and prevents submitting without a choice', async () => {
  render_rating();
  const user = user_event.setup();
  expect(screen.getByRole('button', { name: 'Оценить' })).toBeDisabled();
  expect(screen.queryByRole('radio', { name: '0.5 из 5' })).not.toBeInTheDocument();
  await user.tab();
  expect(screen.getByRole('radio', { name: '1 из 5' })).toHaveFocus();
  await user.keyboard('{ArrowRight}');
  expect(screen.getByRole('radio', { name: '1.5 из 5' })).toBeChecked();
  await user.keyboard('{ArrowLeft}');
  expect(screen.getByRole('radio', { name: '1 из 5' })).toBeChecked();
  expect(screen.getByRole('button', { name: 'Оценить' })).toBeEnabled();
});
