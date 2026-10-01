import { useState, type FormEvent } from 'react';
import { Link } from 'react-router';
import { useMutation, useQuery } from '@tanstack/react-query';
import { api, unwrap } from '../../api/client';
import { all_genres } from '../../api/catalog';
import type { components } from '../../api/generated';
import { query_client } from '../../app/query';
import { EmptyState, ErrorState, LoadingState } from '../../components/States';
import { use_auth } from './AuthProvider';

export function PreferencesPage() {
  const { user, is_loading, error } = use_auth();
  const genres_query = useQuery({
    queryKey: ['genres'],
    queryFn: ({ signal }) => all_genres(signal),
    enabled: !!user,
  });
  const favorites_query = useQuery({
    queryKey: ['favorite_genres', user?.id],
    enabled: !!user,
    queryFn: async ({ signal }) => unwrap(await api.GET('/api/v1/me/favorite-genres', { signal })),
  });
  if (is_loading) return <LoadingState />;
  if (error) return <ErrorState error={error} />;
  if (!user)
    return (
      <div className="panel">
        <h1>Музыка по вашему вкусу</h1>
        <p>Войдите, чтобы выбрать любимые жанры.</p>
        <Link className="button primary" to="/login?next=/preferences">
          Войти
        </Link>
      </div>
    );
  if (genres_query.isPending || favorites_query.isPending) return <LoadingState />;
  if (genres_query.isError || favorites_query.isError)
    return (
      <ErrorState
        error={genres_query.error || favorites_query.error}
        retry={() => {
          void genres_query.refetch();
          void favorites_query.refetch();
        }}
      />
    );
  return (
    <GenreForm
      key={`${user.id}:${favorites_query.data.map((genre) => genre.id).join(',')}`}
      genres={genres_query.data}
      initial_ids={favorites_query.data.map((genre) => genre.id)}
    />
  );
}

function GenreForm({
  genres,
  initial_ids,
}: {
  genres: components['schemas']['GenreOut'][];
  initial_ids: number[];
}) {
  const [selected_ids, set_selected_ids] = useState(initial_ids);
  const mutation = useMutation({
    mutationFn: async () =>
      unwrap(await api.PUT('/api/v1/me/favorite-genres', { body: { genre_ids: selected_ids } })),
    onSuccess: async () => {
      await query_client.invalidateQueries({ queryKey: ['recommendations'] });
      await query_client.invalidateQueries({ queryKey: ['favorite_genres'] });
    },
  });
  function submit(event: FormEvent) {
    event.preventDefault();
    mutation.mutate();
  }
  return (
    <>
      <span className="eyebrow">НАСТРОЙТЕ СВОЮ ВОЛНУ</span>
      <h1>Что вы слушаете?</h1>
      <p className="muted">
        Любимые жанры и ваши оценки влияют на рекомендации. Выбор можно изменить.
      </p>
      <form className="panel form" onSubmit={submit}>
        {!genres.length ? (
          <EmptyState
            title="Жанров пока нет"
            description="Жанры появятся после добавления в каталог."
          />
        ) : (
          <fieldset className="genre-picker">
            <legend>Любимые жанры</legend>
            {genres.map((genre) => (
              <label
                className={selected_ids.includes(genre.id) ? 'genre-selected' : ''}
                key={genre.id}
              >
                <input
                  type="checkbox"
                  checked={selected_ids.includes(genre.id)}
                  onChange={(event) =>
                    set_selected_ids(
                      event.target.checked
                        ? [...selected_ids, genre.id]
                        : selected_ids.filter((id) => id !== genre.id),
                    )
                  }
                />
                {genre.name}
              </label>
            ))}
          </fieldset>
        )}
        <div className="actions">
          <button className="button primary" disabled={mutation.isPending}>
            Сохранить жанры
          </button>
          <button type="button" className="button" onClick={() => set_selected_ids([])}>
            Очистить выбор
          </button>
          <Link to="/recommendations">Перейти к рекомендациям →</Link>
        </div>
        {mutation.isError && <ErrorState error={mutation.error} />}
        {mutation.isSuccess && <p role="status">Предпочтения сохранены.</p>}
      </form>
    </>
  );
}
