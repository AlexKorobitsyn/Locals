import { useState, type FormEvent } from 'react';
import { Link, useNavigate, useParams } from 'react-router';
import { useMutation, useQuery } from '@tanstack/react-query';
import { ArrowDown, ArrowUp, ListPlus, Play, Trash2 } from 'lucide-react';
import { api, unwrap } from '../../api/client';
import { ApiError } from '../../api/errors';
import type { components } from '../../api/generated';
import {
  DESCRIPTION_MAX_LENGTH,
  NAME_MAX_LENGTH,
  PAGE_LIMIT,
  format_duration,
  parse_id,
} from '../../app/constants';
import { invalidate_music } from '../../app/query';
import { Cover } from '../../components/Cover';
import { Pagination } from '../../components/Pagination';
import { EmptyState, ErrorState, LoadingState } from '../../components/States';
import { use_auth } from '../auth/AuthProvider';
import { ImageUpload } from '../studio/ImageUpload';
import { use_player } from '../player/PlayerProvider';
import { RatingBadge } from '../ratings/RatingControl';
import { FavoriteButton } from './FavoriteButton';
import { all_playlist_tracks } from './api';

export function PlaylistPage() {
  const { id } = useParams();
  const { user } = use_auth();
  return <PlaylistContent key={`${id}:${user?.id}`} />;
}

function PlaylistContent() {
  const playlist_id = parse_id(useParams().id);
  const { user } = use_auth();
  const player = use_player();
  const [offset, set_offset] = useState(0);
  const query = useQuery({
    queryKey: ['playlist', user?.id, playlist_id],
    enabled: !!playlist_id,
    queryFn: async ({ signal }) =>
      unwrap(
        await api.GET('/api/v1/playlists/{playlist_id}', {
          params: { path: { playlist_id: playlist_id! } },
          signal,
        }),
      ),
  });
  const editable = !!query.data?.is_owner && query.data.kind !== 'liked';
  const tracks_query = useQuery({
    queryKey: ['playlist_tracks', user?.id, playlist_id, editable ? 'all' : offset],
    enabled: !!query.data,
    queryFn: async ({ signal }) =>
      editable
        ? all_playlist_tracks(playlist_id!, signal)
        : unwrap(
            await api.GET('/api/v1/playlists/{playlist_id}/tracks', {
              params: { path: { playlist_id: playlist_id! }, query: { limit: PAGE_LIMIT, offset } },
              signal,
            }),
          ),
  });
  const changes = useMutation({
    mutationFn: async ({ track_id, direction }: { track_id: number; direction?: number }) => {
      if (direction === undefined)
        return unwrap(
          await api.DELETE('/api/v1/playlists/{playlist_id}/tracks/{track_id}', {
            params: { path: { playlist_id: playlist_id!, track_id } },
          }),
        );
      const track_ids = tracks_query.data!.items.map((item) => item.track.id);
      const index = track_ids.indexOf(track_id);
      const next_index = index + direction;
      if (index < 0 || next_index < 0 || next_index >= track_ids.length) return;
      [track_ids[index], track_ids[next_index]] = [track_ids[next_index]!, track_ids[index]!];
      return unwrap(
        await api.PUT('/api/v1/playlists/{playlist_id}/tracks/order', {
          params: { path: { playlist_id: playlist_id! } },
          body: { track_ids },
        }),
      );
    },
    onSuccess: invalidate_music,
    onError: async (error) => {
      if (error instanceof ApiError && error.status === 409) await tracks_query.refetch();
    },
  });
  if (!playlist_id) return <ErrorState error={new ApiError(404, 'Такого плейлиста нет.')} />;
  if (query.isPending) return <LoadingState />;
  if (query.isError) return <ErrorState error={query.error} retry={() => void query.refetch()} />;
  const playlist = query.data;
  const visible_tracks = editable
    ? tracks_query.data?.items.slice(offset, offset + PAGE_LIMIT)
    : tracks_query.data?.items;
  return (
    <>
      <Link className="back-link" to="/library">
        ← Библиотека
      </Link>
      <div className="detail-hero">
        <Cover large url={playlist.cover_url} name={playlist.name} />
        <div>
          <span className="eyebrow">
            {playlist.kind === 'liked' ? 'ЛЮБИМЫЕ ТРЕКИ' : 'ПЛЕЙЛИСТ'} ·{' '}
            {playlist.visibility === 'private' ? 'ПРИВАТНЫЙ' : 'ПУБЛИЧНЫЙ'}
          </span>
          <h1>{playlist.kind === 'liked' ? 'Мне нравится' : playlist.name}</h1>
          <p className="muted">
            <Link to={`/users/${playlist.owner.id}`}>{playlist.owner.display_name}</Link> ·{' '}
            {playlist.tracks_count} треков
          </p>
          {playlist.description && <p className="preserve-lines">{playlist.description}</p>}
          {playlist.kind !== 'liked' && (
            <FavoriteButton
              entity_type="playlist"
              entity_id={playlist.id}
              is_liked={playlist.is_liked_by_me}
            />
          )}
          {playlist.kind === 'liked' && (
            <p className="muted">
              Треки появляются здесь после лайка. Снимите лайк на странице трека, чтобы убрать его.
            </p>
          )}
        </div>
      </div>
      {editable && <ImageUpload key={playlist.id} target_type="playlist" target_id={playlist.id} />}
      {tracks_query.isPending ? (
        <LoadingState />
      ) : tracks_query.isError ? (
        <ErrorState error={tracks_query.error} retry={() => void tracks_query.refetch()} />
      ) : (
        <>
          {visible_tracks?.length ? (
            <div className="track-list">
              {visible_tracks.map((item) => (
                <article className="track-row" key={item.track.id}>
                  <span className="track-number">{item.position + 1}</span>
                  <button
                    className="icon-button"
                    aria-label={`Слушать ${item.track.title}`}
                    onClick={() =>
                      player.play(
                        tracks_query.data.items.map((entry) => entry.track),
                        tracks_query.data.items.findIndex(
                          (entry) => entry.track.id === item.track.id,
                        ),
                      )
                    }
                  >
                    <Play size={17} />
                  </button>
                  <div className="track-row-title">
                    <Link to={`/tracks/${item.track.id}`}>{item.track.title}</Link>
                    <RatingBadge
                      rating_avg={item.track.rating_avg}
                      my_rating={item.track.my_rating}
                    />
                  </div>
                  <span className="muted">{format_duration(item.track.duration)}</span>
                  <button
                    className="icon-button"
                    aria-label={`Добавить ${item.track.title} в очередь`}
                    onClick={() => player.append(item.track)}
                  >
                    <ListPlus size={18} />
                  </button>
                  {editable && (
                    <div className="actions">
                      <button
                        className="icon-button"
                        aria-label={`Поднять ${item.track.title}`}
                        disabled={changes.isPending || item.position === 0}
                        onClick={() => changes.mutate({ track_id: item.track.id, direction: -1 })}
                      >
                        <ArrowUp size={16} />
                      </button>
                      <button
                        className="icon-button"
                        aria-label={`Опустить ${item.track.title}`}
                        disabled={
                          changes.isPending || item.position + 1 >= tracks_query.data.items.length
                        }
                        onClick={() => changes.mutate({ track_id: item.track.id, direction: 1 })}
                      >
                        <ArrowDown size={16} />
                      </button>
                      <button
                        className="icon-button"
                        aria-label={`Убрать ${item.track.title} из плейлиста`}
                        disabled={changes.isPending}
                        onClick={() => changes.mutate({ track_id: item.track.id })}
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  )}
                </article>
              ))}
            </div>
          ) : (
            <EmptyState
              title="Добавьте музыку в подборку"
              description="Откройте трек и выберите «Добавить в плейлист»."
            />
          )}
          <Pagination total={tracks_query.data.total} offset={offset} on_change={set_offset} />
        </>
      )}
      {changes.isError && <ErrorState error={changes.error} />}
      {editable && (
        <PlaylistEditor key={`${playlist.id}:${playlist.updated_at}`} playlist={playlist} />
      )}
    </>
  );
}

function PlaylistEditor({ playlist }: { playlist: components['schemas']['PlaylistOut'] }) {
  const navigate = useNavigate();
  const [name, set_name] = useState(playlist.name);
  const [description, set_description] = useState(playlist.description || '');
  const [visibility, set_visibility] = useState(playlist.visibility);
  const [confirm_delete, set_confirm_delete] = useState(false);
  const mutation = useMutation({
    mutationFn: async (remove: boolean) =>
      remove
        ? unwrap(
            await api.DELETE('/api/v1/playlists/{playlist_id}', {
              params: { path: { playlist_id: playlist.id } },
            }),
          )
        : unwrap(
            await api.PATCH('/api/v1/playlists/{playlist_id}', {
              params: { path: { playlist_id: playlist.id } },
              body: { name: name.trim(), description: description.trim() || null, visibility },
            }),
          ),
    onSuccess: async (_, remove) => {
      await invalidate_music();
      if (remove) navigate('/library', { replace: true });
    },
  });
  function submit(event: FormEvent) {
    event.preventDefault();
    mutation.mutate(false);
  }
  return (
    <form className="panel form" onSubmit={submit}>
      <h2>Настройки плейлиста</h2>
      <label>
        Название
        <input
          value={name}
          onChange={(event) => set_name(event.target.value)}
          required
          maxLength={NAME_MAX_LENGTH}
        />
      </label>
      <label>
        Описание
        <textarea
          value={description}
          onChange={(event) => set_description(event.target.value)}
          maxLength={DESCRIPTION_MAX_LENGTH}
          rows={3}
        />
      </label>
      <label>
        Доступ
        <select
          value={visibility}
          onChange={(event) => set_visibility(event.target.value as typeof visibility)}
        >
          <option value="private">Только мне</option>
          <option value="public">Всем</option>
        </select>
      </label>
      <div className="actions">
        <button className="button primary" disabled={mutation.isPending || !name.trim()}>
          Сохранить плейлист
        </button>
        <button
          className="text-button"
          type="button"
          disabled={mutation.isPending}
          onClick={() => set_confirm_delete(true)}
        >
          Удалить плейлист
        </button>
      </div>
      {confirm_delete && (
        <div className="confirmation" role="alertdialog" aria-label="Удаление плейлиста">
          <p>Удалить плейлист «{playlist.name}»?</p>
          <button
            className="button danger"
            type="button"
            disabled={mutation.isPending}
            onClick={() => mutation.mutate(true)}
          >
            Удалить
          </button>
          <button className="button" type="button" onClick={() => set_confirm_delete(false)}>
            Отмена
          </button>
        </div>
      )}
      {mutation.isError && <ErrorState error={mutation.error} />}
    </form>
  );
}
