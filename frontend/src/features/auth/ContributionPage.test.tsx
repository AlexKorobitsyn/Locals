import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import user_event from '@testing-library/user-event';
import { QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router';
import { query_client } from '../../app/query';
import { ContributionForm } from './ProgressPage';
import { ProposalCard } from './ContributionPage';
import type { components } from '../../api/generated';

vi.mock('./AuthProvider', () => ({
  use_auth: () => ({
    user: { id: 2, level: 'green' },
    experience: {
      experience_points: 0,
      experience_level: 1,
      votes_required: 5,
      contribution_limit: 2,
    },
  }),
}));
beforeEach(() => query_client.clear());
afterEach(() => {
  query_client.clear();
  vi.unstubAllGlobals();
});
function wrap(child: React.ReactNode) {
  return render(
    <QueryClientProvider client={query_client}>
      <MemoryRouter>{child}</MemoryRouter>
    </QueryClientProvider>,
  );
}
it('lets a newcomer propose lyrics and genres without an experience gate', async () => {
  wrap(<ContributionForm target_type="track" target_id={42} />);
  const user = user_event.setup();
  await user.click(screen.getByRole('button', { name: 'Предложить исправление' }));
  expect(screen.getByRole('option', { name: 'Текст песни' })).toBeInTheDocument();
  expect(screen.getByRole('option', { name: 'Жанры' })).toBeInTheDocument();
  expect(screen.getByRole('option', { name: 'Название' })).toBeInTheDocument();
});
it('supports community votes while keeping the owner approval requirement visible', async () => {
  const fetch_mock = vi.fn(async (_input: RequestInfo | URL) => Response.json({}));
  vi.stubGlobal('fetch', fetch_mock);
  const proposal: components['schemas']['ContributionOut'] = {
    id: 1,
    user_id: 3,
    reviewer_id: null,
    target_type: 'track',
    target_id: 42,
    field: 'lyrics',
    status: 'pending',
    before: { lyrics: 'Owner version' },
    proposed: { lyrics: 'Community version' },
    reason: null,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    votes_count: 3,
    eligible_votes_count: 2,
    is_voted_by_me: false,
    requires_owner: true,
    can_review: false,
    can_approve: false,
  };
  wrap(<ProposalCard proposal={proposal} />);
  expect(screen.getByText(/Голоса помогают ему выбрать правку/)).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Одобрить' })).not.toBeInTheDocument();
  await user_event.setup().click(screen.getByRole('button', { name: 'Поддержать предложение' }));
  expect(fetch_mock).toHaveBeenCalledOnce();
  expect((fetch_mock.mock.calls[0]?.[0] as Request).url).toContain('/contributions/1/vote');
});
