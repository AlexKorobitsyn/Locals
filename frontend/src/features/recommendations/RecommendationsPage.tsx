import { useState } from 'react';
import { Link } from 'react-router';
import { useQuery } from '@tanstack/react-query';
import { Play } from 'lucide-react';
import { api, unwrap } from '../../api/client';
import type { components } from '../../api/generated';
import { PAGE_LIMIT } from '../../app/constants';
import { Pagination } from '../../components/Pagination';
import { EmptyState, ErrorState, LoadingState } from '../../components/States';
import { use_auth } from '../auth/AuthProvider';
import { use_player } from '../player/PlayerProvider';
import { CatalogCard } from '../catalog/CatalogPage';

type Reason = NonNullable<components['schemas']['RecommendedTrack']['reasons']>[number];
const REASONS: Record<Reason, string> = {
  favorite_genres: 'Ваши любимые жанры',
  high_rated_genres: 'Вы высоко оцениваете эти жанры',
  low_rated_genres: 'Ваши низкие оценки уменьшили приоритет',
  community_rating: 'Учтён рейтинг слушателей',
  catalog_fallback: 'Находка из общего каталога',
};

export function RecommendationsPage() {
  const { user } = use_auth();
  const player = use_player();
  const [offset, set_offset] = useState(0);
  const [playable_only, set_playable_only] = useState(false);
  const query = useQuery({
    queryKey: ['recommendations', user?.id, offset, playable_only],
    queryFn: async ({ signal }) =>
      unwrap(
        await api.GET('/api/v1/recommendations/tracks', {
          params: { query: { limit: PAGE_LIMIT, offset, playable_only } },
          signal,
        }),
      ),
  });
  const playable_query = useQuery({
    queryKey: ['recommendations', user?.id, 'queue'],
    queryFn: async ({ signal }) =>
      unwrap(
        await api.GET('/api/v1/recommendations/tracks', {
          params: { query: { limit: PAGE_LIMIT, playable_only: true } },
          signal,
        }),
      ),
  });
  return (
    <>
      <div className="discovery-hero">
        <div>
          <span className="eyebrow">НЕЗАВИСИМАЯ СЦЕНА / СТОРОНА А</span>
          <h1>
            Музыка вне эфира<span className="heading-dot">.</span>
          </h1>
          <p>
            {query.data?.mode === 'personalized'
              ? 'Музыка, подобранная по вашим жанрам и оценкам.'
              : 'Находки из каталога с учётом оценок слушателей.'}
          </p>
          <div className="actions">
            <button
              className="button primary"
              disabled={!playable_query.data?.items.length}
              onClick={() => player.play(playable_query.data!.items)}
            >
              <Play size={18} />
              Слушать подборку
            </button>
            <Link className="button" to={user ? '/preferences' : '/register'}>
              {user ? 'Настроить вкус' : 'Найти свою музыку'}
            </Link>
          </div>
        </div>
        <div className="record-art" aria-hidden="true">
          <div className="record-label">
            L
            <span>
              LOCALS
              <br />
              SIDE A
            </span>
          </div>
        </div>
      </div>
      <div className="section-heading">
        <h2>{query.data?.mode === 'personalized' ? 'Подобрано для вас' : 'Стоит услышать'}</h2>
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={playable_only}
            onChange={(event) => {
              set_playable_only(event.target.checked);
              set_offset(0);
            }}
          />
          Только с аудио
        </label>
      </div>
      {playable_query.isError && (
        <ErrorState error={playable_query.error} retry={() => void playable_query.refetch()} />
      )}
      {query.isPending ? (
        <LoadingState />
      ) : query.isError ? (
        <ErrorState error={query.error} retry={() => void query.refetch()} />
      ) : (
        <>
          {query.data.items.length ? (
            <div className="catalog-grid recommendation-grid">
              {query.data.items.map((track) => (
                <div key={track.id}>
                  <CatalogCard item={track} kind="tracks" is_playable={track.is_playable} />
                  <div className="recommendation-reasons">
                    {!track.is_playable && <strong>Аудио пока нет</strong>}
                    {(track.reasons || []).map((reason) => (
                      <span key={reason}>{REASONS[reason]}</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              title="Новые находки ещё появятся"
              description="Вы уже знаете доступную музыку или в каталоге пока нет подходящих треков."
            />
          )}
          <Pagination total={query.data.total} offset={offset} on_change={set_offset} />
        </>
      )}
    </>
  );
}
