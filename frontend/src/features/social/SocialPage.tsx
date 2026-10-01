import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router';
import { api, unwrap } from '../../api/client';
import type { components } from '../../api/generated';
import { PAGE_LIMIT, format_datetime } from '../../app/constants';
import { AuthRequired } from '../../components/AuthRequired';
import { Cover } from '../../components/Cover';
import { Pagination } from '../../components/Pagination';
import { EmptyState, ErrorState, LoadingState } from '../../components/States';
import { use_auth } from '../auth/AuthProvider';
import { FollowButton } from './FollowButton';

const TARGET_PATHS: Record<string, string> = {
  user: 'users',
  artist: 'artists',
  album: 'albums',
  track: 'tracks',
  venue: 'venues',
  event: 'events',
  playlist: 'playlists',
};
const TARGET_LABELS: Record<string, string> = {
  user: 'профиль',
  artist: 'артиста',
  album: 'альбом',
  track: 'трек',
  venue: 'площадку',
  event: 'событие',
  playlist: 'плейлист',
};
const ACTION_LABELS: Record<string, string> = {
  artist_created: 'добавил артиста',
  artist_updated: 'обновил артиста',
  album_created: 'опубликовал альбом',
  album_updated: 'обновил альбом',
  track_created: 'опубликовал трек',
  track_updated: 'обновил трек',
  venue_created: 'добавил площадку',
  venue_updated: 'обновил площадку',
  event_created: 'добавил событие',
  event_updated: 'обновил событие',
  event_deleted: 'удалил событие',
  rating_set: 'оценил запись',
  rating_deleted: 'удалил оценку',
  review_created: 'написал рецензию',
  review_updated: 'обновил рецензию',
  review_deleted: 'удалил рецензию',
  favorite_added: 'сохранил в избранное',
  favorite_removed: 'убрал из избранного',
  follow_added: 'подписался',
  follow_removed: 'отписался',
  playlist_created: 'создал плейлист',
  playlist_updated: 'обновил плейлист',
  playlist_track_added: 'добавил трек в плейлист',
  playlist_track_removed: 'убрал трек из плейлиста',
  playlist_tracks_reordered: 'изменил порядок треков',
  audio_attached: 'обновил аудио',
  image_attached: 'обновил изображение',
};

function FollowingCard({ entry }: { entry: components['schemas']['FollowOut'] }) {
  const { user } = use_auth();
  const query = useQuery({
    queryKey: ['following', user?.id, entry.target_type, entry.target_id],
    queryFn: async ({ signal }) => {
      if (entry.target_type === 'user') {
        const item = unwrap(
          await api.GET('/api/v1/users/{user_id}', {
            params: { path: { user_id: entry.target_id } },
            signal,
          }),
        );
        return { name: item.display_name, image: item.avatar_url };
      }
      if (entry.target_type === 'artist') {
        const item = unwrap(
          await api.GET('/api/v1/artists/{artist_id}', {
            params: { path: { artist_id: entry.target_id } },
            signal,
          }),
        );
        return { name: item.name, image: item.image_url };
      }
      const item = unwrap(
        await api.GET('/api/v1/venues/{venue_id}', {
          params: { path: { venue_id: entry.target_id } },
          signal,
        }),
      );
      return { name: item.name, image: item.cover_url };
    },
  });
  return (
    <article className="panel social-card">
      {query.isPending ? (
        <LoadingState />
      ) : query.isError ? (
        <ErrorState error={query.error} retry={() => void query.refetch()} />
      ) : (
        <Link
          className="social-identity"
          to={`/${TARGET_PATHS[entry.target_type]}/${entry.target_id}`}
        >
          <Cover url={query.data.image} name={query.data.name} />
          <div>
            <span className="eyebrow">
              {entry.target_type === 'user'
                ? 'СЛУШАТЕЛЬ'
                : entry.target_type === 'artist'
                  ? 'АРТИСТ'
                  : 'ПЛОЩАДКА'}
            </span>
            <h3>{query.data.name}</h3>
          </div>
        </Link>
      )}
      <FollowButton target_type={entry.target_type} target_id={entry.target_id} followed />
    </article>
  );
}

function SocialContent({ following }: { following: boolean }) {
  const { user } = use_auth();
  const [offset, set_offset] = useState(0);
  const query = useQuery({
    queryKey: [following ? 'following' : 'feed', user?.id, offset],
    queryFn: async ({ signal }) => {
      const options = { params: { query: { limit: PAGE_LIMIT, offset } }, signal };
      return following
        ? unwrap(await api.GET('/api/v1/me/following', options))
        : unwrap(await api.GET('/api/v1/me/feed', options));
    },
  });
  return (
    <>
      <div className="section-heading">
        <div className="page-intro">
          <span className="eyebrow">СООБЩЕСТВО / LOCALS</span>
          <h1>
            {following ? 'Ваш круг' : 'Что нового'}
            <span className="heading-dot">.</span>
          </h1>
          <p className="muted">
            {following
              ? 'Артисты, слушатели и места, за которыми вы следите.'
              : 'Новые записи и события тех, на кого вы подписаны.'}
          </p>
        </div>
        <Link className="button" to={following ? '/feed' : '/following'}>
          {following ? 'Открыть ленту' : 'Мои подписки'}
        </Link>
      </div>
      {query.isPending ? (
        <LoadingState />
      ) : query.isError ? (
        <ErrorState error={query.error} retry={() => void query.refetch()} />
      ) : (
        <>
          {!query.data.items.length ? (
            <EmptyState
              title={following ? 'Подписки появятся здесь' : 'В ленте пока тихо'}
              description="Откройте артиста или площадку и нажмите «Подписаться»."
            />
          ) : (
            <div className="social-list">
              {query.data.items.map((item) =>
                'target_type' in item && 'follower_id' in item ? (
                  <FollowingCard key={item.id} entry={item} />
                ) : (
                  'actor' in item && (
                    <article className="panel feed-card" key={item.id}>
                      <span className="eyebrow">
                        <time dateTime={item.created_at}>{format_datetime(item.created_at)}</time>
                      </span>
                      <p>
                        {item.actor ? (
                          <Link to={`/users/${item.actor.id}`}>
                            <strong>{item.actor.display_name}</strong>
                          </Link>
                        ) : (
                          'Участник'
                        )}{' '}
                        {'action' in item &&
                          (ACTION_LABELS[item.action] || 'поделился обновлением')}
                      </p>
                      {TARGET_PATHS[item.target_type] && (
                        <Link
                          className="text-button"
                          to={`/${TARGET_PATHS[item.target_type]}/${item.target_id}`}
                        >
                          Открыть {TARGET_LABELS[item.target_type]} →
                        </Link>
                      )}
                    </article>
                  )
                ),
              )}
            </div>
          )}
          <Pagination offset={offset} total={query.data.total} on_change={set_offset} />
        </>
      )}
    </>
  );
}

export function SocialPage({ following = false }: { following?: boolean }) {
  return (
    <AuthRequired>
      <SocialContent key={String(following)} following={following} />
    </AuthRequired>
  );
}
