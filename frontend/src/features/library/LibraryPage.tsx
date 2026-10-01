import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router';
import { useMutation, useQuery } from '@tanstack/react-query';
import { api, unwrap } from '../../api/client';
import { NAME_MAX_LENGTH, PAGE_LIMIT } from '../../app/constants';
import { invalidate_music } from '../../app/query';
import { Cover } from '../../components/Cover';
import { Pagination } from '../../components/Pagination';
import { EmptyState, ErrorState, LoadingState } from '../../components/States';
import { use_auth } from '../auth/AuthProvider';

type LibraryScope = 'own' | 'saved' | 'public';

export function LibraryPage() {
  const { user, is_loading, error } = use_auth();
  const navigate = useNavigate();
  const [scope, set_scope] = useState<LibraryScope>('own');
  const [offset, set_offset] = useState(0);
  const [name, set_name] = useState('');
  const [is_public, set_is_public] = useState(false);
  const query = useQuery({
    queryKey: ['library', user?.id, scope, offset],
    enabled: scope === 'public' || !!user,
    queryFn: async ({ signal }) => {
      const options = { params: { query: { limit: PAGE_LIMIT, offset } }, signal };
      if (scope === 'public') return unwrap(await api.GET('/api/v1/playlists', options));
      if (scope === 'saved') return unwrap(await api.GET('/api/v1/me/saved-playlists', options));
      return unwrap(await api.GET('/api/v1/me/playlists', options));
    },
  });
  const creation = useMutation({
    mutationFn: async () =>
      unwrap(
        await api.POST('/api/v1/playlists', {
          body: { name: name.trim(), visibility: is_public ? 'public' : 'private' },
        }),
      ),
    onSuccess: async (playlist) => {
      await invalidate_music();
      navigate(`/playlists/${playlist.id}`);
    },
  });
  function create(event: FormEvent) {
    event.preventDefault();
    creation.mutate();
  }
  return (
    <>
      <div className="page-intro">
        <span className="eyebrow">МУЗЫКА, К КОТОРОЙ ВОЗВРАЩАЮТСЯ</span>
        <h1>
          Библиотека<span className="heading-dot">.</span>
        </h1>
        <p className="muted">Любимые треки, собственные подборки и находки других слушателей.</p>
      </div>
      <div className="tabs" role="group" aria-label="Раздел библиотеки">
        {(
          [
            ['own', 'Мои плейлисты'],
            ['saved', 'Сохранённые'],
            ['public', 'Публичные'],
          ] as const
        ).map(([value, label]) => (
          <button
            key={value}
            aria-pressed={scope === value}
            onClick={() => {
              set_scope(value);
              set_offset(0);
            }}
          >
            {label}
          </button>
        ))}
      </div>
      {is_loading ? (
        <LoadingState />
      ) : error ? (
        <ErrorState error={error} />
      ) : scope !== 'public' && !user ? (
        <div className="panel">
          <h2>Соберите свою музыку</h2>
          <p>Войдите, чтобы открыть личную библиотеку.</p>
          <Link className="button primary" to="/login?next=/library">
            Войти
          </Link>
        </div>
      ) : query.isPending ? (
        <LoadingState />
      ) : query.isError ? (
        <ErrorState error={query.error} retry={() => void query.refetch()} />
      ) : (
        <>
          {query.data.items.length ? (
            <div className="catalog-grid">
              {query.data.items.map((playlist) => (
                <Link
                  className="catalog-card playlist-card"
                  key={playlist.id}
                  to={`/playlists/${playlist.id}`}
                >
                  <Cover url={playlist.cover_url} name={playlist.name} />
                  <div className="card-body">
                    <span className="eyebrow">
                      {playlist.kind === 'liked'
                        ? 'ЛЮБИМЫЕ ТРЕКИ'
                        : playlist.visibility === 'private'
                          ? 'ПРИВАТНЫЙ ПЛЕЙЛИСТ'
                          : 'ПУБЛИЧНЫЙ ПЛЕЙЛИСТ'}
                    </span>
                    <h3>{playlist.kind === 'liked' ? 'Мне нравится' : playlist.name}</h3>
                    <p className="muted">{playlist.tracks_count} треков</p>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <EmptyState
              title="Подборок пока нет"
              description="Создайте свою или сохраните публичную подборку другого слушателя."
            />
          )}
          <Pagination total={query.data.total} offset={offset} on_change={set_offset} />
        </>
      )}
      {user && scope === 'own' && (
        <form className="panel form" onSubmit={create}>
          <h2>Новая подборка</h2>
          <label>
            Название
            <input
              value={name}
              onChange={(event) => set_name(event.target.value)}
              required
              maxLength={NAME_MAX_LENGTH}
            />
          </label>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={is_public}
              onChange={(event) => set_is_public(event.target.checked)}
            />
            Публичный плейлист
          </label>
          <button className="button primary" disabled={creation.isPending || !name.trim()}>
            Создать плейлист
          </button>
          {creation.isError && <ErrorState error={creation.error} />}
        </form>
      )}
    </>
  );
}
