import { useState } from 'react';
import { Link, useSearchParams } from 'react-router';
import { useMutation, useQuery } from '@tanstack/react-query';
import type { components } from '../../api/generated';
import { AuthRequired } from '../../components/AuthRequired';
import { ErrorState, LoadingState, EmptyState } from '../../components/States';
import { Pagination } from '../../components/Pagination';
import { DESCRIPTION_MAX_LENGTH, MAX_PAGE_LIMIT, PAGE_LIMIT } from '../../app/constants';
import { invalidate_music } from '../../app/query';
import { admin_request } from '../admin/api';
import { use_auth } from './AuthProvider';

type Proposal = components['schemas']['ContributionOut'];
const FIELD_LABELS: Record<string, string> = {
  lyrics: 'Текст песни',
  genres: 'Жанры',
  metadata: 'Название',
  publication: 'Новая площадка или событие',
};
const STATUS_LABELS: Record<string, string> = {
  pending: 'Голосование открыто',
  approved: 'Принято',
  rejected: 'Отклонено',
};
export const LEVEL_NAMES = [
  'Новичок',
  'Слушатель',
  'Искатель',
  'Знаток',
  'Рецензент',
  'Куратор',
  'Проводник',
  'Амбассадор',
  'Легенда',
];

export function ContributionPage() {
  return (
    <AuthRequired>
      <Community />
    </AuthRequired>
  );
}
function Community() {
  const [offset, set_offset] = useState(0);
  const [search] = useSearchParams();
  const { user, experience } = use_auth();
  const filters = ['target_type', 'target_id']
    .map((key) => (search.get(key) ? `&${key}=${encodeURIComponent(search.get(key)!)}` : ''))
    .join('');
  const query = useQuery({
    queryKey: ['contributions', 'community', user?.id, offset, filters],
    queryFn: () =>
      admin_request<{ items: Proposal[]; total: number }>(
        `/contributions?limit=${PAGE_LIMIT}&offset=${offset}${filters}`,
      ),
  });
  return (
    <>
      <div className="page-intro">
        <span className="eyebrow">СООБЩЕСТВО / LOCALS</span>
        <h1>Предложения сообщества</h1>
        <p>Правки может предложить каждый. За принятый вклад начисляется опыт.</p>
        <p className="muted">
          Для публикации нужны {experience?.votes_required || 5} голосов участников второго уровня и
          выше. Версия владельца меняется только с его одобрения. Сейчас у вас лимит{' '}
          {experience?.contribution_limit || 2} открытых предложений.
        </p>
      </div>
      {query.isPending ? (
        <LoadingState />
      ) : query.isError ? (
        <ErrorState error={query.error} />
      ) : !query.data.items.length ? (
        <EmptyState title="Открытых предложений пока нет" />
      ) : (
        query.data.items.map((proposal) => <ProposalCard key={proposal.id} proposal={proposal} />)
      )}
      {query.data && <Pagination total={query.data.total} offset={offset} on_change={set_offset} />}
    </>
  );
}

export function ProposalCard({ proposal }: { proposal: Proposal }) {
  const { user, experience } = use_auth();
  const [reason, set_reason] = useState('');
  const [decision, set_decision] = useState<'approve' | 'reject' | null>(null);
  const genres = useQuery({
    queryKey: ['catalog_picker', 'proposal_genres'],
    enabled: proposal.field === 'genres',
    queryFn: async () => {
      const items: components['schemas']['GenreOut'][] = [];
      for (let offset = 0; ; offset += MAX_PAGE_LIMIT) {
        const page = await admin_request<{
          items: components['schemas']['GenreOut'][];
          total: number;
        }>(`/genres?limit=${MAX_PAGE_LIMIT}&offset=${offset}`);
        items.push(...page.items);
        if (items.length >= page.total || !page.items.length) return items;
      }
    },
  });
  function value_text(value: Record<string, unknown>) {
    if (proposal.field === 'lyrics') return String(value.lyrics || 'Текст отсутствует');
    if (proposal.field === 'genres')
      return (
        ((value.genre_ids || []) as number[])
          .map((id) => genres.data?.find((genre) => genre.id === id)?.name || `Жанр №${id}`)
          .join(', ') || 'Жанры не указаны'
      );
    if (proposal.field === 'metadata') return String(value.name || '');
    const labels: Record<string, string> = {
      name: 'Название',
      description: 'Описание',
      address: 'Адрес',
      city_id: 'Город №',
      lat: 'Широта',
      lng: 'Долгота',
      starts_at: 'Начало',
      stop_at: 'Окончание',
      website: 'Сайт',
      capacity: 'Вместимость',
      venue_id: 'Площадка №',
    };
    return (
      Object.entries(value)
        .filter(([key, val]) => labels[key] && val != null)
        .map(([key, val]) => `${labels[key]}: ${String(val)}`)
        .join('\n') || 'Ожидает публикации'
    );
  }
  const vote = useMutation({
    mutationFn: () =>
      admin_request(
        `/contributions/${proposal.id}/vote`,
        proposal.is_voted_by_me ? 'DELETE' : 'PUT',
      ),
    onSuccess: invalidate_music,
  });
  const withdraw = useMutation({
    mutationFn: () => admin_request(`/contributions/${proposal.id}`, 'DELETE'),
    onSuccess: invalidate_music,
  });
  const [confirm_withdraw, set_confirm_withdraw] = useState(false);
  const review = useMutation({
    mutationFn: () =>
      admin_request(`/contributions/${proposal.id}/review`, 'PUT', {
        decision,
        reason: reason || null,
      }),
    onSuccess: async () => {
      set_decision(null);
      await invalidate_music();
    },
  });
  const can_vote = proposal.status === 'pending' && user && user.id !== proposal.user_id;
  const can_review = proposal.status === 'pending' && proposal.can_review;
  const can_withdraw = user?.id === proposal.user_id && proposal.status !== 'approved';
  return (
    <article className="panel admin-proposal">
      <div className="section-heading">
        <h3>
          {FIELD_LABELS[proposal.field]} · предложение №{proposal.id}
        </h3>
        {proposal.field !== 'publication' ||
        proposal.can_review ||
        user?.id === proposal.user_id ? (
          <Link to={`/${proposal.target_type}s/${proposal.target_id}`}>Открыть запись</Link>
        ) : null}
      </div>
      <p className="proposal-meta">
        <Link to={`/users/${proposal.user_id}`}>Профиль автора</Link>
        <span className={`proposal-status proposal-status-${proposal.status}`}>
          {STATUS_LABELS[proposal.status]}
        </span>
      </p>
      <div className="admin-comparison">
        <div>
          <strong>Сейчас</strong>
          <pre className="admin-diff">{value_text(proposal.before)}</pre>
        </div>
        <div>
          <strong>Предлагается</strong>
          <pre className="admin-diff">{value_text(proposal.proposed)}</pre>
        </div>
      </div>
      <p>
        {proposal.votes_count} голосов · засчитывается для принятия: {proposal.eligible_votes_count}
        /{experience?.votes_required || 5}
      </p>
      {proposal.requires_owner && (
        <p className="muted">
          У записи есть версия владельца. Голоса помогают ему выбрать правку, но не заменяют её
          автоматически.
        </p>
      )}
      {(can_vote || can_review || can_withdraw || proposal.reason) && (
        <div className="proposal-footer">
          <div className="proposal-actions">
            {can_vote && (
              <button
                className={`button ${proposal.is_voted_by_me ? 'primary' : ''}`}
                disabled={vote.isPending}
                onClick={() => vote.mutate()}
              >
                {proposal.is_voted_by_me ? 'Убрать голос' : 'Поддержать предложение'}
              </button>
            )}
            {can_review &&
              (decision ? (
                <div role="alertdialog" className="confirmation" aria-label="Решение по заявке">
                  <p>
                    {decision === 'approve' ? 'Принять предложение?' : 'Отклонить предложение?'}
                  </p>
                  <div className="actions">
                    <button
                      className={`button ${decision === 'reject' ? 'danger' : 'primary'}`}
                      disabled={review.isPending}
                      onClick={() => review.mutate()}
                    >
                      Подтвердить
                    </button>
                    <button
                      className="button"
                      disabled={review.isPending}
                      onClick={() => set_decision(null)}
                    >
                      Отмена
                    </button>
                  </div>
                </div>
              ) : (
                <div className="actions">
                  <button
                    className="button primary"
                    disabled={!proposal.can_approve}
                    onClick={() => set_decision('approve')}
                  >
                    Одобрить
                  </button>
                  <button className="button danger" onClick={() => set_decision('reject')}>
                    Отклонить
                  </button>
                </div>
              ))}
            {can_withdraw &&
              (confirm_withdraw ? (
                <div className="confirmation" role="alertdialog">
                  <p>Отозвать предложение?</p>
                  <div className="actions">
                    <button
                      className="button danger"
                      disabled={withdraw.isPending}
                      onClick={() => withdraw.mutate()}
                    >
                      Подтвердить отзыв
                    </button>
                    <button className="button" onClick={() => set_confirm_withdraw(false)}>
                      Отмена
                    </button>
                  </div>
                </div>
              ) : (
                <button className="button" onClick={() => set_confirm_withdraw(true)}>
                  Отозвать предложение
                </button>
              ))}
          </div>
          {can_review ? (
            <label className="proposal-comment">
              Комментарий к решению
              <textarea
                rows={3}
                placeholder="Необязательно"
                maxLength={DESCRIPTION_MAX_LENGTH}
                value={reason}
                onChange={(event) => set_reason(event.target.value)}
              />
            </label>
          ) : proposal.reason ? (
            <div className="proposal-comment">
              <strong>Комментарий к решению</strong>
              <p>{proposal.reason}</p>
            </div>
          ) : null}
        </div>
      )}
      {withdraw.isError && <ErrorState error={withdraw.error} />}
      {vote.isError && <ErrorState error={vote.error} />}
      {review.isError && <ErrorState error={review.error} />}
    </article>
  );
}
