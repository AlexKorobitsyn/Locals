import { useEffect, useRef, useState, type FormEvent } from 'react';
import { Link, useParams, useSearchParams } from 'react-router';
import { useMutation, useQuery } from '@tanstack/react-query';
import { api, unwrap } from '../../api/client';
import { ApiError } from '../../api/errors';
import type { CatalogKind } from '../../api/catalog';
import type { components } from '../../api/generated';
import {
  DESCRIPTION_MAX_LENGTH,
  LYRICS_MAX_LENGTH,
  NAME_MAX_LENGTH,
  PERCENT_TOTAL,
  parse_id,
} from '../../app/constants';
import { invalidate_music } from '../../app/query';
import { AuthRequired } from '../../components/AuthRequired';
import { CityPicker } from '../../components/CityPicker';
import { EntityPicker } from '../../components/EntityPicker';
import { GenrePicker } from '../../components/GenrePicker';
import { ErrorState, LoadingState } from '../../components/States';
import { use_auth } from '../auth/AuthProvider';
import { ArtistsField, type ArtistSelection } from './ArtistsField';
import { FileField, use_upload_limits } from './FileField';
import { upload_file, validate_file } from './media';

type Artist = components['schemas']['ArtistOut'];
type Album = components['schemas']['AlbumOut'];
type Track = components['schemas']['TrackOut'];
type Record = Artist | Album | Track;
type Media = components['schemas']['MediaOut'];
const ENTITY_NAMES = { artists: 'Артист', albums: 'Альбом', tracks: 'Трек' };
async function get_record(kind: CatalogKind, id: number, signal?: AbortSignal): Promise<Record> {
  if (kind === 'artists')
    return unwrap(
      await api.GET('/api/v1/artists/{artist_id}', { params: { path: { artist_id: id } }, signal }),
    );
  if (kind === 'albums')
    return unwrap(
      await api.GET('/api/v1/albums/{album_id}', { params: { path: { album_id: id } }, signal }),
    );
  return unwrap(
    await api.GET('/api/v1/tracks/{track_id}', { params: { path: { track_id: id } }, signal }),
  );
}

export function CatalogEditorPage({ kind }: { kind: CatalogKind }) {
  return (
    <AuthRequired>
      <EditorLoader kind={kind} />
    </AuthRequired>
  );
}
function EditorLoader({ kind }: { kind: CatalogKind }) {
  const { id: raw_id } = useParams();
  const id = parse_id(raw_id);
  const { user } = use_auth();
  const [search] = useSearchParams();
  const artist_id = parse_id(search.get('artist_id') || undefined);
  const album_id = parse_id(search.get('album_id') || undefined);
  const query = useQuery({
    queryKey: ['detail', user?.id, 'editor', kind, id],
    enabled: !!id,
    queryFn: ({ signal }) => get_record(kind, id!, signal),
  });
  const initial_artist = useQuery({
    queryKey: ['catalog_picker', user?.id, 'artists', artist_id],
    enabled: !id && !!artist_id && kind !== 'artists',
    queryFn: async ({ signal }) =>
      unwrap(
        await api.GET('/api/v1/artists/{artist_id}', {
          params: { path: { artist_id: artist_id! } },
          signal,
        }),
      ),
  });
  const initial_album = useQuery({
    queryKey: ['catalog_picker', user?.id, 'albums', album_id],
    enabled: !id && !!album_id && kind === 'tracks',
    queryFn: async ({ signal }) =>
      unwrap(
        await api.GET('/api/v1/albums/{album_id}', {
          params: { path: { album_id: album_id! } },
          signal,
        }),
      ),
  });
  if (raw_id && !id) return <ErrorState error={new ApiError(404, 'Запись не найдена.')} />;
  if (
    (id && query.isPending) ||
    (!id && artist_id && kind !== 'artists' && initial_artist.isPending) ||
    (!id && album_id && kind === 'tracks' && initial_album.isPending)
  )
    return <LoadingState />;
  if ((id && query.isError) || initial_artist.isError || initial_album.isError)
    return (
      <ErrorState
        error={query.error || initial_artist.error || initial_album.error}
        retry={() => {
          if (id) void query.refetch();
          if (artist_id) void initial_artist.refetch();
          if (album_id) void initial_album.refetch();
        }}
      />
    );
  if (
    (id && !query.data?.is_owner) ||
    (initial_artist.data && !initial_artist.data.is_owner) ||
    (initial_album.data && !initial_album.data.is_owner)
  )
    return (
      <ErrorState
        error={
          new ApiError(403, 'Редактировать и использовать для публикации можно только свои записи.')
        }
      />
    );
  return (
    <CatalogEditor
      key={`${user!.id}:${kind}:${id}:${artist_id}:${album_id}`}
      kind={kind}
      initial={query.data || null}
      initial_artist={initial_artist.data}
      initial_album={initial_album.data}
    />
  );
}

function CatalogEditor({
  kind,
  initial,
  initial_artist,
  initial_album,
}: {
  kind: CatalogKind;
  initial: Record | null;
  initial_artist?: Artist;
  initial_album?: Album;
}) {
  const limits = use_upload_limits();
  const [name, set_name] = useState(
    initial ? ('name' in initial ? initial.name : initial.title) : '',
  );
  const [bio, set_bio] = useState(initial && 'bio' in initial ? initial.bio || '' : '');
  const [city_id, set_city_id] = useState(
    initial && 'city' in initial ? initial.city?.id || null : null,
  );
  const [genre_ids, set_genre_ids] = useState(initial?.genres?.map((genre) => genre.id) || []);
  const [release_date, set_release_date] = useState(
    initial && 'release_date' in initial ? initial.release_date || '' : '',
  );
  const [lyrics, set_lyrics] = useState(initial && 'lyrics' in initial ? initial.lyrics || '' : '');
  const [album_id, set_album_id] = useState(
    initial && 'album' in initial ? initial.album?.id || null : initial_album?.id || null,
  );
  const [artists, set_artists] = useState<ArtistSelection[]>(() =>
    initial && 'artist_credits' in initial
      ? (initial.artist_credits || []).map((credit) => ({
          artist_id: credit.artist.id,
          name: credit.artist.name,
          role: credit.role,
        }))
      : initial && 'artists' in initial
        ? (initial.artists || []).map((artist) => ({
            artist_id: artist.id,
            name: artist.name,
            role: 'primary',
          }))
        : initial_artist
          ? [{ artist_id: initial_artist.id, name: initial_artist.name, role: 'primary' }]
          : initial_album
            ? (initial_album.artists || []).map((artist) => ({
                artist_id: artist.id,
                name: artist.name,
                role: 'primary',
              }))
            : [],
  );
  const [audio_file, set_audio_file] = useState<File | null>(null);
  const [image_file, set_image_file] = useState<File | null>(null);
  const [progress, set_progress] = useState(0);
  const [phase, set_phase] = useState('');
  const [published, set_published] = useState<Record | null>(null);
  const [created_id, set_created_id] = useState<number | null>(null);
  const created = useRef<Record | null>(initial);
  const audio_cache = useRef<{ file: File; media: Media } | null>(null);
  const image_cache = useRef<{ file: File; media: Media } | null>(null);
  const controller_ref = useRef<AbortController | null>(null);
  useEffect(() => () => controller_ref.current?.abort(), []);
  const mutation = useMutation({
    mutationFn: async () => {
      if (!limits.data) throw new ApiError(503, 'Настройки загрузки ещё не получены.');
      if (audio_file) validate_file(audio_file, 'audio', limits.data);
      if (image_file) validate_file(image_file, 'image', limits.data);
      if (kind !== 'artists' && !artists.length)
        throw new ApiError(422, 'Добавьте хотя бы одного своего артиста.');
      if (kind === 'tracks' && artists.some((artist) => !artist.role.trim()))
        throw new ApiError(422, 'Укажите роли участников записи.');
      if (kind === 'tracks' && !initial && !audio_file)
        throw new ApiError(422, 'Выберите аудиофайл для публикации.');
      const controller = new AbortController();
      controller_ref.current = controller;
      const signal = controller.signal;
      if (audio_file && audio_cache.current?.file !== audio_file) {
        set_phase('Загружаем аудио');
        set_progress(0);
        audio_cache.current = {
          file: audio_file,
          media: await upload_file(audio_file, 'audio', limits.data, set_progress, signal),
        };
      }
      set_phase('Сохраняем запись');
      let record = created.current;
      if (kind === 'artists') {
        const body = { name: name.trim(), bio: bio.trim() || null, city_id, genre_ids };
        if (!record) record = unwrap(await api.POST('/api/v1/artists', { body, signal }));
        else if (initial)
          record = unwrap(
            await api.PATCH('/api/v1/artists/{artist_id}', {
              params: { path: { artist_id: record.id } },
              body,
              signal,
            }),
          );
      } else if (kind === 'albums') {
        const body = {
          title: name.trim(),
          release_date: release_date || null,
          artist_ids: [...new Set(artists.map((artist) => artist.artist_id))],
          genre_ids,
        };
        if (!record) record = unwrap(await api.POST('/api/v1/albums', { body, signal }));
        else if (initial)
          record = unwrap(
            await api.PATCH('/api/v1/albums/{album_id}', {
              params: { path: { album_id: record.id } },
              body,
              signal,
            }),
          );
      } else {
        const body = {
          title: name.trim(),
          album_id,
          lyrics: lyrics.trim() || null,
          genre_ids,
          artist_credits: artists.map(({ artist_id, role }) => ({ artist_id, role: role.trim() })),
        };
        if (!record) {
          const duration = audio_cache.current?.media.duration;
          if (!duration || !Number.isFinite(duration))
            throw new ApiError(422, 'Не удалось определить длительность аудио.');
          record = unwrap(
            await api.POST('/api/v1/tracks', {
              body: { ...body, duration: Math.ceil(duration) },
              signal,
            }),
          );
        } else if (initial)
          record = unwrap(
            await api.PATCH('/api/v1/tracks/{track_id}', {
              params: { path: { track_id: record.id } },
              body,
              signal,
            }),
          );
      }
      created.current = record!;
      set_created_id(record!.id);
      if (audio_file && audio_cache.current) {
        set_phase('Подключаем аудио');
        unwrap(
          await api.PUT('/api/v1/tracks/{track_id}/audio', {
            params: { path: { track_id: record!.id } },
            body: { media_id: audio_cache.current.media.id },
            signal,
          }),
        );
      }
      if (image_file) {
        if (image_cache.current?.file !== image_file) {
          set_phase('Загружаем обложку');
          set_progress(0);
          image_cache.current = {
            file: image_file,
            media: await upload_file(image_file, 'image', limits.data, set_progress, signal),
          };
        }
        set_phase('Подключаем обложку');
        unwrap(
          await api.PUT('/api/v1/images/{target_type}/{target_id}', {
            params: {
              path: {
                target_type: kind === 'artists' ? 'artist' : kind === 'albums' ? 'album' : 'track',
                target_id: record!.id,
              },
            },
            body: { media_id: image_cache.current.media.id },
            signal,
          }),
        );
      }
      return record!;
    },
    onSuccess: async (record) => {
      set_published(record);
      await invalidate_music();
    },
    onError: async () => {
      await invalidate_music();
    },
  });
  function submit(event: FormEvent) {
    event.preventDefault();
    mutation.mutate();
  }
  if (published)
    return (
      <section className="panel publication-success">
        <span className="eyebrow">В ЭФИРЕ / LOCALS</span>
        <h1>
          {initial
            ? 'Изменения сохранены'
            : kind === 'artists'
              ? 'Артист создан'
              : kind === 'albums'
                ? 'Релиз добавлен'
                : 'Трек опубликован'}
        </h1>
        <p>{name}</p>
        <div className="actions">
          <Link className="button primary" to={`/${kind}/${published.id}`}>
            Открыть {kind === 'artists' ? 'артиста' : kind === 'albums' ? 'альбом' : 'трек'}
          </Link>
          {kind === 'artists' && (
            <>
              <Link className="button" to={`/studio/albums/new?artist_id=${published.id}`}>
                Добавить альбом
              </Link>
              <Link className="button" to={`/studio/tracks/new?artist_id=${published.id}`}>
                Загрузить трек
              </Link>
            </>
          )}
          {kind === 'albums' && (
            <Link className="button" to={`/studio/tracks/new?album_id=${published.id}`}>
              Загрузить трек
            </Link>
          )}
          <Link to="/studio">Вернуться в студию</Link>
        </div>
      </section>
    );
  return (
    <>
      <Link className="back-link" to="/studio">
        ← Студия
      </Link>
      <div className="page-intro">
        <span className="eyebrow">ПУБЛИКАЦИЯ / {ENTITY_NAMES[kind].toUpperCase()}</span>
        <h1>
          {initial ? 'Редактировать' : 'Новая запись'}
          <span className="heading-dot">.</span>
        </h1>
        <p className="muted">
          {kind === 'tracks'
            ? 'Аудио станет доступно для прослушивания после загрузки и сохранения.'
            : 'Название, история и обложка — у каждой записи есть своё лицо.'}
        </p>
      </div>
      {limits.isPending ? (
        <LoadingState />
      ) : limits.isError ? (
        <ErrorState error={limits.error} retry={() => void limits.refetch()} />
      ) : (
        <form className="panel form editor-form" onSubmit={submit}>
          <fieldset
            className="form-fields"
            disabled={mutation.isPending || (!!created_id && !initial)}
          >
            <label>
              {kind === 'artists' ? 'Имя артиста' : 'Название'}
              <input
                value={name}
                onChange={(event) => set_name(event.target.value)}
                required
                maxLength={NAME_MAX_LENGTH}
              />
            </label>
            {kind === 'artists' ? (
              <>
                <label>
                  Об артисте
                  <textarea
                    value={bio}
                    onChange={(event) => set_bio(event.target.value)}
                    maxLength={DESCRIPTION_MAX_LENGTH}
                    rows={5}
                  />
                </label>
                <CityPicker
                  value={city_id}
                  on_change={set_city_id}
                  initial_name={initial && 'city' in initial ? initial.city?.name : undefined}
                />
              </>
            ) : (
              <>
                <ArtistsField
                  value={artists}
                  on_change={set_artists}
                  with_roles={kind === 'tracks'}
                />
                {kind === 'albums' ? (
                  <label>
                    Дата релиза
                    <input
                      type="date"
                      value={release_date}
                      onChange={(event) => set_release_date(event.target.value)}
                    />
                  </label>
                ) : (
                  <>
                    <EntityPicker
                      kind="albums"
                      label="Альбом"
                      value={album_id}
                      on_change={set_album_id}
                      owner_only
                    />
                    <label>
                      Текст трека · необязательно
                      <textarea
                        value={lyrics}
                        onChange={(event) => set_lyrics(event.target.value)}
                        maxLength={LYRICS_MAX_LENGTH}
                        rows={6}
                      />
                    </label>
                  </>
                )}
              </>
            )}
            <GenrePicker value={genre_ids} on_change={set_genre_ids} />
          </fieldset>
          <fieldset className="form-fields" disabled={mutation.isPending}>
            {kind === 'tracks' && (
              <FileField
                kind="audio"
                file={audio_file}
                on_change={set_audio_file}
                limits={limits.data}
                required={!initial}
              />
            )}
            <FileField
              kind="image"
              file={image_file}
              on_change={set_image_file}
              limits={limits.data}
            />
          </fieldset>
          {mutation.isPending && (
            <div className="upload-progress" role="status">
              <span>
                {phase}
                {phase.startsWith('Загружаем') ? ` · ${progress}%` : '…'}
              </span>
              {phase.startsWith('Загружаем') && (
                <progress value={progress} max={PERCENT_TOTAL} aria-label="Прогресс загрузки" />
              )}
              <button
                className="text-button"
                type="button"
                onClick={() => controller_ref.current?.abort()}
              >
                Отменить
              </button>
            </div>
          )}
          {mutation.isError && (
            <>
              <ErrorState
                error={
                  mutation.error instanceof DOMException && mutation.error.name === 'AbortError'
                    ? new ApiError(0, 'Загрузка отменена. Можно продолжить позже.')
                    : mutation.error
                }
              />
              {created_id && !initial && (
                <p className="muted">
                  Запись уже создана. Повторная попытка подключит файлы к ней.{' '}
                  <Link to={`/studio/${kind}/${created_id}`}>Открыть редактор</Link>
                </p>
              )}
            </>
          )}
          <div className="actions">
            <button className="button primary" disabled={mutation.isPending || !name.trim()}>
              {created_id && !initial
                ? 'Повторить подключение файлов'
                : initial
                  ? 'Сохранить изменения'
                  : kind === 'tracks'
                    ? 'Опубликовать трек'
                    : kind === 'artists'
                      ? 'Создать артиста'
                      : 'Создать альбом'}
            </button>
            <Link to="/studio">Вернуться в студию</Link>
          </div>
        </form>
      )}
    </>
  );
}
