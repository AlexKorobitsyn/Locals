import { can_create_scene, can_moderate } from '../../app/permissions';
import { useState, type FormEvent } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Link, useNavigate, useParams, useSearchParams } from 'react-router';
import { api, unwrap } from '../../api/client';
import type { components } from '../../api/generated';
import { ApiError } from '../../api/errors';
import {
  DESCRIPTION_MAX_LENGTH,
  LATITUDE_MAX,
  LATITUDE_MIN,
  LONGITUDE_MAX,
  LONGITUDE_MIN,
  MAX_DATABASE_INTEGER,
  MAX_RELATIONS,
  NAME_MAX_LENGTH,
  datetime_input,
  parse_id,
} from '../../app/constants';
import { invalidate_music } from '../../app/query';
import { AuthRequired } from '../../components/AuthRequired';
import { CityPicker } from '../../components/CityPicker';
import { EntityPicker } from '../../components/EntityPicker';
import { ErrorState, LoadingState } from '../../components/States';
import { use_auth } from '../auth/AuthProvider';
import { can_edit, use_event_types } from './EventPages';
import { LocationPicker } from './LocationPicker';
import { MAP_COORDINATE_PRECISION } from './map_constants';
import { use_reverse_address } from './use_reverse_address';

type Venue = components['schemas']['VenueOut'];
type Event = components['schemas']['EventOut'];
type EventType = components['schemas']['EventType'];

function EditorLoader({ venues }: { venues: boolean }) {
  const { user, experience } = use_auth();
  const parameter = useParams().id;
  const id = parse_id(parameter);
  const [search] = useSearchParams();
  const types = use_event_types();
  const query = useQuery({
    queryKey: [venues ? 'venues' : 'events', user?.id, id],
    enabled: !!id,
    queryFn: async ({ signal }) =>
      venues
        ? unwrap(
            await api.GET('/api/v1/venues/{venue_id}', {
              params: { path: { venue_id: id! } },
              signal,
            }),
          )
        : unwrap(
            await api.GET('/api/v1/events/{event_id}', {
              params: { path: { event_id: id! } },
              signal,
            }),
          ),
  });
  if (parameter && !id) return <ErrorState error={new ApiError(404, 'Такой записи нет.')} />;
  if ((id && query.isPending) || (!venues && types.isPending)) return <LoadingState />;
  if (id && query.isError)
    return <ErrorState error={query.error} retry={() => void query.refetch()} />;
  if (!venues && types.isError)
    return <ErrorState error={types.error} retry={() => void types.refetch()} />;
  if (!id && !can_create_scene(user?.level, experience))
    return (
      <ErrorState error={new ApiError(403, 'Войдите, чтобы предложить площадку или событие.')} />
    );
  if (query.data && !can_edit(query.data.is_owner, user?.level))
    return (
      <ErrorState
        error={new ApiError(403, 'Редактировать эту запись может владелец или модератор.')}
      />
    );
  return (
    <SceneEditor
      key={`${user?.id}:${venues}:${id || 'new'}`}
      venues={venues}
      initial={query.data}
      types={types.data || []}
      initial_venue_id={parse_id(search.get('venue_id') || undefined)}
    />
  );
}

function SceneEditor({
  venues,
  initial,
  types,
  initial_venue_id,
}: {
  venues: boolean;
  initial?: Venue | Event;
  types: EventType[];
  initial_venue_id: number | null;
}) {
  const { user } = use_auth();
  const direct_publish = user?.scene_verified || can_moderate(user?.level);
  const navigate = useNavigate();
  const [name, set_name] = useState(initial?.name || '');
  const [description, set_description] = useState(initial?.description || '');
  const [city_id, set_city_id] = useState<number | null>(initial?.city?.id || null);
  const [venue_id, set_venue_id] = useState<number | null>(
    initial && 'venue' in initial ? initial.venue?.id || null : initial_venue_id,
  );
  const [lat, set_lat] = useState(initial?.lat == null ? '' : String(initial.lat));
  const [lng, set_lng] = useState(initial?.lng == null ? '' : String(initial.lng));
  const [address, set_address] = useState(
    initial && 'address' in initial ? initial.address || '' : '',
  );
  const reverse = use_reverse_address(set_address);
  const [website, set_website] = useState(
    initial && 'website' in initial ? initial.website || '' : '',
  );
  const [capacity, set_capacity] = useState(
    initial && 'capacity' in initial && initial.capacity != null ? String(initial.capacity) : '',
  );
  const [starts_at, set_starts_at] = useState(
    initial && 'starts_at' in initial ? datetime_input(initial.starts_at) : '',
  );
  const [stop_at, set_stop_at] = useState(
    initial && 'stop_at' in initial ? datetime_input(initial.stop_at) : '',
  );
  const [type_ids, set_type_ids] = useState<number[]>(
    initial && 'type_event' in initial
      ? initial.type_event?.map((type) => type.id) || []
      : types[0]
        ? [types[0].id]
        : [],
  );
  const mutation = useMutation({
    mutationFn: async () => {
      const common = { name: name.trim(), description: description.trim() || null };
      if (venues) {
        if (!city_id || lat === '' || lng === '')
          throw new ApiError(422, 'Для площадки нужны город и координаты.');
        const body = {
          ...common,
          city_id,
          lat: Number(lat),
          lng: Number(lng),
          address: address.trim() || null,
          website: website.trim() || null,
          capacity: capacity === '' ? null : Number(capacity),
        };
        return initial
          ? unwrap(
              await api.PATCH('/api/v1/venues/{venue_id}', {
                params: { path: { venue_id: initial.id } },
                body,
              }),
            )
          : unwrap(await api.POST('/api/v1/venues', { body }));
      }
      if (!venue_id && !city_id) throw new ApiError(422, 'Выберите площадку или город.');
      if (!type_ids.length) throw new ApiError(422, 'Выберите хотя бы один тип события.');
      if (stop_at && new Date(stop_at) <= new Date(starts_at))
        throw new ApiError(422, 'Окончание должно быть позже начала.');
      if ((lat === '') !== (lng === ''))
        throw new ApiError(422, 'Укажите обе координаты или оставьте обе пустыми.');
      const body = {
        ...common,
        venue_id,
        ...(city_id && !venue_id ? { city_id } : {}),
        ...(lat !== '' && !venue_id ? { lat: Number(lat), lng: Number(lng) } : {}),
        starts_at: new Date(starts_at).toISOString(),
        stop_at: stop_at ? new Date(stop_at).toISOString() : null,
        type_event_ids: type_ids,
      };
      return initial
        ? unwrap(
            await api.PATCH('/api/v1/events/{event_id}', {
              params: { path: { event_id: initial.id } },
              body,
            }),
          )
        : unwrap(await api.POST('/api/v1/events', { body }));
    },
    onSuccess: async (record) => {
      await invalidate_music();
      navigate(`/${venues ? 'venues' : 'events'}/${record.id}`);
    },
  });
  function submit(event: FormEvent) {
    event.preventDefault();
    mutation.mutate();
  }
  return (
    <>
      <Link className="back-link" to={`/${venues ? 'venues' : 'events'}`}>
        ← {venues ? 'Площадки' : 'События'}
      </Link>
      <div className="page-intro">
        <span className="eyebrow">ЖИВАЯ СЦЕНА / ПУБЛИКАЦИЯ</span>
        <h1>
          {initial ? 'Редактировать' : venues ? 'Новая площадка' : 'Новое событие'}
          <span className="heading-dot">.</span>
        </h1>
      </div>
      <form className="panel form editor-form" onSubmit={submit}>
        <fieldset className="form-fields" disabled={mutation.isPending}>
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
              rows={5}
            />
          </label>
          {!venues && (
            <EntityPicker
              kind="venues"
              label="Площадка"
              value={venue_id}
              on_change={(value) => {
                set_venue_id(value);
                set_lat('');
                set_lng('');
                set_city_id(null);
              }}
            />
          )}
          {(venues || !venue_id) && (
            <CityPicker
              value={city_id}
              on_change={(value) => {
                set_city_id(value);
                if (value !== city_id) {
                  set_lat('');
                  set_lng('');
                  if (venues) {
                    reverse.cancel();
                    set_address('');
                  }
                }
              }}
              required
              initial_name={initial?.city?.name}
            />
          )}
          <LocationPicker
            venues={venues}
            city_id={city_id}
            venue_id={venue_id}
            lat={lat}
            lng={lng}
            on_venue={(value) => {
              set_venue_id(value);
              set_lat('');
              set_lng('');
              set_city_id(null);
            }}
            on_point={(point) => {
              if (!venues) set_venue_id(null);
              set_lat(point.lat.toFixed(MAP_COORDINATE_PRECISION));
              set_lng(point.lng.toFixed(MAP_COORDINATE_PRECISION));
              if (venues) {
                set_address('');
                reverse.lookup(point);
              }
            }}
          />
          <div className="form-row">
            <label>
              Широта{!venues && ' · необязательно'}
              <input
                type="number"
                min={LATITUDE_MIN}
                max={LATITUDE_MAX}
                step="any"
                value={lat}
                disabled={!venues && !!venue_id}
                onChange={(event) => {
                  set_lat(event.target.value);
                  if (venues) {
                    reverse.cancel();
                    set_address('');
                  }
                }}
                required={venues}
              />
            </label>
            <label>
              Долгота{!venues && ' · необязательно'}
              <input
                type="number"
                min={LONGITUDE_MIN}
                max={LONGITUDE_MAX}
                step="any"
                value={lng}
                disabled={!venues && !!venue_id}
                onChange={(event) => {
                  set_lng(event.target.value);
                  if (venues) {
                    reverse.cancel();
                    set_address('');
                  }
                }}
                required={venues}
              />
            </label>
          </div>
          {!venues && (
            <small className="muted">
              При выборе площадки используются её город и координаты. Без площадки выберите город и
              точку на карте.
            </small>
          )}
          {venues ? (
            <>
              <label>
                Адрес
                <input
                  value={address}
                  onChange={(event) => {
                    reverse.cancel();
                    set_address(event.target.value);
                  }}
                  maxLength={DESCRIPTION_MAX_LENGTH}
                />
              </label>
              <small className="muted" aria-live="polite">
                {reverse.state === 'loading'
                  ? 'Определяем адрес выбранной точки…'
                  : reverse.state === 'ready'
                    ? 'Адрес найден. При необходимости уточните его вручную.'
                    : reverse.state === 'missing'
                      ? 'У этой точки нет адреса в справочнике. Введите его вручную.'
                      : reverse.state === 'error'
                        ? 'Не удалось определить адрес. Введите его вручную или повторите поиск.'
                        : 'Выберите точку на карте — адрес заполнится автоматически.'}{' '}
                {(reverse.state === 'error' || reverse.state === 'missing') && (
                  <button type="button" className="text-button" onClick={reverse.retry}>
                    Повторить поиск адреса
                  </button>
                )}
              </small>
              <small className="muted">
                Адреса:{' '}
                <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">
                  © OpenStreetMap contributors
                </a>
              </small>
              <label>
                Вместимость
                <input
                  type="number"
                  min={0}
                  max={MAX_DATABASE_INTEGER}
                  step={1}
                  value={capacity}
                  onChange={(event) => set_capacity(event.target.value)}
                />
              </label>
              <label>
                Сайт
                <input
                  type="url"
                  placeholder="https://"
                  value={website}
                  onChange={(event) => set_website(event.target.value)}
                />
              </label>
              <small className="muted">Обложку можно загрузить после создания площадки.</small>
            </>
          ) : (
            <>
              <div className="form-row">
                <label>
                  Начало
                  <input
                    type="datetime-local"
                    value={starts_at}
                    onChange={(event) => set_starts_at(event.target.value)}
                    required
                  />
                </label>
                <label>
                  Окончание · необязательно
                  <input
                    type="datetime-local"
                    value={stop_at}
                    onChange={(event) => set_stop_at(event.target.value)}
                    min={starts_at}
                  />
                </label>
              </div>
              <small className="muted">
                Время вводится в часовом поясе вашего устройства:{' '}
                {Intl.DateTimeFormat().resolvedOptions().timeZone}.
              </small>
              <fieldset className="genre-picker">
                <legend>Тип события</legend>
                {types.map((type) => (
                  <label className="checkbox-label" key={type.id}>
                    <input
                      type="checkbox"
                      checked={type_ids.includes(type.id)}
                      disabled={!type_ids.includes(type.id) && type_ids.length >= MAX_RELATIONS}
                      onChange={(event) =>
                        set_type_ids(
                          event.target.checked
                            ? [...type_ids, type.id]
                            : type_ids.filter((id) => id !== type.id),
                        )
                      }
                    />
                    {type.name}
                  </label>
                ))}
              </fieldset>
            </>
          )}
        </fieldset>
        {mutation.isError && <ErrorState error={mutation.error} />}
        <button
          className="button primary"
          disabled={mutation.isPending || !name.trim() || reverse.state === 'loading'}
        >
          {mutation.isPending
            ? 'Сохраняем…'
            : initial
              ? 'Сохранить изменения'
              : venues
                ? direct_publish
                  ? 'Создать площадку'
                  : 'Предложить площадку'
                : direct_publish
                  ? 'Опубликовать событие'
                  : 'Предложить событие'}
        </button>
      </form>
    </>
  );
}

export function SceneEditorPage({ venues = false }: { venues?: boolean }) {
  return (
    <AuthRequired>
      <EditorLoader venues={venues} />
    </AuthRequired>
  );
}
