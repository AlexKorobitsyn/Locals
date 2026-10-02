import { Select } from '../../components/Select';
import { can_edit_public, can_create_scene } from '../../app/permissions';
import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Link, useNavigate, useParams, useSearchParams } from 'react-router';
import { CalendarDays, MapPin } from 'lucide-react';
import { api, unwrap } from '../../api/client';
import { ApiError } from '../../api/errors';
import { PAGE_LIMIT, format_datetime, parse_id } from '../../app/constants';
import { invalidate_music } from '../../app/query';
import { CityPicker } from '../../components/CityPicker';
import { Cover } from '../../components/Cover';
import { Pagination } from '../../components/Pagination';
import { EmptyState, ErrorState, LoadingState } from '../../components/States';
import { use_auth } from '../auth/AuthProvider';
import { FavoriteButton } from '../library/FavoriteButton';
import { RatingBadge, RatingControl } from '../ratings/RatingControl';
import { Reviews } from '../reviews/Reviews';
import { FollowButton } from '../social/FollowButton';
import { ImageUpload } from '../studio/ImageUpload';
import { SceneMap } from './SceneMap';
import { MAP_PLACE_ZOOM } from './map_constants';

export function can_edit(is_owner: boolean | undefined, level?: string) {
  return can_edit_public(is_owner, level);
}
export function use_event_types() {
  return useQuery({
    queryKey: ['event_types'],
    queryFn: async ({ signal }) => unwrap(await api.GET('/api/v1/event-types', { signal })),
  });
}
const EVENT_SORTS = ['starts_at', '-starts_at', 'name', '-created_at'] as const;
const VENUE_SORTS = ['name', '-rating_avg', '-ratings_count', '-created_at'] as const;
function valid_date(value: string | null) {
  return value && Number.isFinite(new Date(value).getTime())
    ? new Date(value).toISOString()
    : undefined;
}

export function ScenePage({ venues = false }: { venues?: boolean }) {
  const { user, experience } = use_auth();
  const [search, set_search] = useSearchParams();
  const city_id = parse_id(search.get('city_id') || undefined);
  const offset = Math.max(0, Number(search.get('offset')) || 0);
  const sort_values = venues ? VENUE_SORTS : EVENT_SORTS;
  const sort = sort_values.find((value) => value === search.get('sort')) || sort_values[0];
  const types = use_event_types();
  const starts_after = valid_date(search.get('starts_after'));
  const starts_before = valid_date(search.get('starts_before'));
  const date_error =
    !venues &&
    ((!!search.get('starts_after') && !starts_after) ||
      (!!search.get('starts_before') && !starts_before) ||
      (!!starts_after && !!starts_before && starts_before <= starts_after));
  function change_filter(key: string, value: string) {
    set_search((previous) => {
      const next = new URLSearchParams(previous);
      next.delete('offset');
      if (value) next.set(key, value);
      else next.delete(key);
      return next;
    });
  }
  const query = useQuery({
    queryKey: [venues ? 'venues' : 'events', user?.id, search.toString()],
    enabled: !date_error,
    queryFn: async ({ signal }) => {
      const common = { limit: PAGE_LIMIT, offset, sort, city_id: city_id || undefined };
      return venues
        ? unwrap(await api.GET('/api/v1/venues', { params: { query: common }, signal }))
        : unwrap(
            await api.GET('/api/v1/events', {
              params: {
                query: {
                  ...common,
                  starts_after,
                  starts_before,
                  venue_id: parse_id(search.get('venue_id') || undefined) || undefined,
                  type_event_id: parse_id(search.get('type_event_id') || undefined) || undefined,
                },
              },
              signal,
            }),
          );
    },
  });
  return (
    <>
      <div className="section-heading">
        <div className="page-intro">
          <span className="eyebrow">ЖИВАЯ СЦЕНА / LOCALS</span>
          <h1>
            {venues ? 'Места силы' : 'После заката'}
            <span className="heading-dot">.</span>
          </h1>
          <p className="muted">
            {venues
              ? 'Площадки, на которых музыка звучит вживую.'
              : 'Концерты, сеты и встречи. Найдите свой вечер.'}
          </p>
        </div>
        {can_create_scene(user?.level, experience) && (
          <Link className="button primary" to={`/${venues ? 'venues' : 'events'}/new`}>
            {venues ? 'Добавить площадку' : 'Добавить событие'}
          </Link>
        )}
      </div>
      <div className="actions scene-view-switch">
        <Link
          className="button"
          to={`/map?${new URLSearchParams({ ...Object.fromEntries(search), layer: venues ? 'venues' : 'events' })}`}
        >
          <MapPin size={18} />
          {venues ? 'Карта площадок' : 'Карта событий'}
        </Link>
        {!venues && search.get('venue_id') && (
          <span className="muted">Показана афиша выбранной площадки.</span>
        )}
      </div>
      <div className="panel form scene-filters">
        <CityPicker
          value={city_id}
          on_change={(value) => change_filter('city_id', value ? String(value) : '')}
        />
        <label>
          Сортировка
          <Select
            label="Сортировка"
            value={sort}
            on_change={(next_value) => change_filter('sort', next_value)}
          >
            {sort_values.map((value) => (
              <option key={value} value={value}>
                {
                  {
                    starts_at: 'Ближайшие сначала',
                    '-starts_at': 'Поздние сначала',
                    name: 'По названию',
                    '-created_at': 'Недавно добавленные',
                    '-rating_avg': 'По рейтингу',
                    '-ratings_count': 'По числу оценок',
                  }[value]
                }
              </option>
            ))}
          </Select>
        </label>
        {!venues && (
          <>
            <label>
              С даты
              <input
                type="datetime-local"
                value={search.get('starts_after') || ''}
                onChange={(event) => change_filter('starts_after', event.target.value)}
              />
            </label>
            <label>
              До даты
              <input
                type="datetime-local"
                value={search.get('starts_before') || ''}
                onChange={(event) => change_filter('starts_before', event.target.value)}
              />
            </label>
            <label>
              Тип события
              <Select
                label="Тип события"
                value={search.get('type_event_id') || ''}
                on_change={(next_value) => change_filter('type_event_id', next_value)}
              >
                <option value="">Все типы</option>
                {types.data?.map((type) => (
                  <option key={type.id} value={type.id}>
                    {type.name}
                  </option>
                ))}
              </Select>
            </label>
            <small className="muted">
              Даты и время — в часовом поясе вашего устройства:{' '}
              {Intl.DateTimeFormat().resolvedOptions().timeZone}.
            </small>
            {types.isError && <ErrorState error={types.error} retry={() => void types.refetch()} />}
          </>
        )}
        <button className="text-button" onClick={() => set_search({})}>
          Сбросить фильтры
        </button>
      </div>
      {date_error ? (
        <p className="field-error" role="alert">
          Проверьте даты: конец периода должен быть позже начала.
        </p>
      ) : query.isPending ? (
        <LoadingState />
      ) : query.isError ? (
        <ErrorState error={query.error} retry={() => void query.refetch()} />
      ) : (
        <>
          {!query.data.items.length ? (
            <EmptyState
              title="Ничего не найдено"
              description="Попробуйте другой город или период."
            />
          ) : (
            <div className="scene-grid">
              {query.data.items.map((item) => (
                <article className="panel scene-card" key={item.id}>
                  {'cover_url' in item && (
                    <Link to={`/venues/${item.id}`}>
                      <Cover url={item.cover_url} name={item.name} />
                    </Link>
                  )}
                  <span className="eyebrow">{item.city?.name || 'ЛОКАЛЬНАЯ СЦЕНА'}</span>
                  <h2>
                    <Link to={`/${venues ? 'venues' : 'events'}/${item.id}`}>{item.name}</Link>
                  </h2>
                  {'starts_at' in item ? (
                    <>
                      <p>
                        <CalendarDays size={16} />
                        <time dateTime={item.starts_at}>{format_datetime(item.starts_at)}</time>
                      </p>
                      {item.venue && (
                        <p>
                          <MapPin size={16} />
                          <Link to={`/venues/${item.venue.id}`}>{item.venue.name}</Link>
                        </p>
                      )}
                    </>
                  ) : (
                    'rating_avg' in item && (
                      <RatingBadge
                        rating_avg={item.rating_avg}
                        ratings_count={item.ratings_count}
                        my_rating={item.my_rating}
                      />
                    )
                  )}
                </article>
              ))}
            </div>
          )}
          <Pagination
            total={query.data.total}
            offset={offset}
            on_change={(value) =>
              set_search((previous) => {
                const next = new URLSearchParams(previous);
                next.set('offset', String(value));
                return next;
              })
            }
          />
        </>
      )}
    </>
  );
}

export function EventPage() {
  const id = parse_id(useParams().id);
  const { user } = use_auth();
  const navigate = useNavigate();
  const [confirm_delete, set_confirm_delete] = useState(false);
  const query = useQuery({
    queryKey: ['events', user?.id, id],
    enabled: !!id,
    queryFn: async ({ signal }) =>
      unwrap(
        await api.GET('/api/v1/events/{event_id}', { params: { path: { event_id: id! } }, signal }),
      ),
  });
  const deletion = useMutation({
    mutationFn: async () =>
      unwrap(
        await api.DELETE('/api/v1/events/{event_id}', { params: { path: { event_id: id! } } }),
      ),
    onSuccess: async () => {
      await invalidate_music();
      navigate('/events');
    },
  });
  const attendance = useMutation({
    mutationFn: async () =>
      unwrap(
        await (query.data?.is_going_by_me
          ? api.DELETE('/api/v1/events/{event_id}/attendance', {
              params: { path: { event_id: id! } },
            })
          : api.PUT('/api/v1/events/{event_id}/attendance', {
              params: { path: { event_id: id! } },
            })),
      ),
    onSuccess: invalidate_music,
  });
  if (!id) return <ErrorState error={new ApiError(404, 'Такого события нет.')} />;
  if (query.isPending) return <LoadingState />;
  if (query.isError) return <ErrorState error={query.error} retry={() => void query.refetch()} />;
  const event = query.data;
  return (
    <>
      <Link className="back-link" to="/events">
        ← Все события
      </Link>
      <section className="panel event-hero">
        <span className="eyebrow">{event.city?.name || 'ЖИВАЯ СЦЕНА'}</span>
        <h1>{event.name}</h1>
        {event.publication_status !== 'published' && (
          <p role="status">
            Предложение{' '}
            {event.publication_status === 'rejected' ? 'отклонено' : 'ожидает принятия сообществом'}
            . <Link to="/contributions">Открыть предложения</Link>
          </p>
        )}
        {event.publication_status === 'published' && (
          <>
            <p>{event.attendees_count} участников</p>
            {user ? (
              <button
                className="button primary"
                disabled={attendance.isPending}
                onClick={() => attendance.mutate()}
              >
                {event.is_going_by_me ? 'Я не иду' : 'Я иду'}
              </button>
            ) : (
              <Link className="button" to="/login">
                Войти и отметить «Я иду»
              </Link>
            )}
            {attendance.isError && <ErrorState error={attendance.error} />}
          </>
        )}
        <p className="event-date">
          <CalendarDays size={22} />
          <time dateTime={event.starts_at}>{format_datetime(event.starts_at)}</time>
          {event.stop_at && (
            <>
              {' '}
              — <time dateTime={event.stop_at}>{format_datetime(event.stop_at)}</time>
            </>
          )}
        </p>
        <small className="muted">
          Часовой пояс устройства: {Intl.DateTimeFormat().resolvedOptions().timeZone}.
        </small>
        {event.venue && (
          <p>
            <Link to={`/venues/${event.venue.id}`}>{event.venue.name}</Link>
          </p>
        )}
        <div className="genre-tags">
          {event.type_event?.map((type) => (
            <span key={type.id}>{type.name}</span>
          ))}
        </div>
        <div className="actions">
          {event.publication_status === 'published' && (
            <FavoriteButton
              entity_type="event"
              entity_id={id}
              is_liked={event.is_liked_by_me || false}
            />
          )}
          {user && can_edit(event.is_owner, user.level) && (
            <>
              {event.publication_status === 'published' && (
                <Link className="button" to={`/events/${id}/edit`}>
                  Редактировать
                </Link>
              )}
              <button className="text-button" onClick={() => set_confirm_delete(true)}>
                Удалить событие
              </button>
            </>
          )}
        </div>
        {confirm_delete && (
          <div className="confirmation">
            <p>Удалить «{event.name}»? Восстановить событие будет нельзя.</p>
            <button
              className="button danger"
              disabled={deletion.isPending}
              onClick={() => deletion.mutate()}
            >
              Подтвердить удаление
            </button>
            <button
              className="button"
              disabled={deletion.isPending}
              onClick={() => set_confirm_delete(false)}
            >
              Отмена
            </button>
          </div>
        )}
        {deletion.isError && <ErrorState error={deletion.error} />}
      </section>
      {event.lat != null && event.lng != null && (
        <section className="panel">
          <h2>Где проходит</h2>
          <SceneMap
            compact
            focus={{ lat: event.lat, lng: event.lng }}
            focus_zoom={MAP_PLACE_ZOOM}
            markers={[
              {
                key: `event:${event.id}`,
                title: event.venue?.name || event.name,
                lat: event.lat,
                lng: event.lng,
                kind: event.venue ? 'active_venue' : 'event',
              },
            ]}
          />
          <Link
            className="text-button"
            to={`/map?city_id=${event.city?.id || ''}&lat=${event.lat}&lng=${event.lng}&${event.venue ? `venue_id=${event.venue.id}` : `event_id=${event.id}`}`}
          >
            Открыть карту событий →
          </Link>
        </section>
      )}
      {event.description && (
        <section className="panel">
          <h2>О событии</h2>
          <p className="preserve-lines">{event.description}</p>
        </section>
      )}
      {event.user_id && (
        <Link className="text-button" to={`/users/${event.user_id}`}>
          Профиль организатора →
        </Link>
      )}
    </>
  );
}

export function VenuePage() {
  const id = parse_id(useParams().id);
  const { user, experience } = use_auth();
  const query = useQuery({
    queryKey: ['venues', user?.id, id],
    enabled: !!id,
    queryFn: async ({ signal }) =>
      unwrap(
        await api.GET('/api/v1/venues/{venue_id}', { params: { path: { venue_id: id! } }, signal }),
      ),
  });
  if (!id) return <ErrorState error={new ApiError(404, 'Такой площадки нет.')} />;
  if (query.isPending) return <LoadingState />;
  if (query.isError) return <ErrorState error={query.error} retry={() => void query.refetch()} />;
  const venue = query.data;
  return (
    <>
      <Link className="back-link" to="/venues">
        ← Все площадки
      </Link>
      <div className="detail-hero">
        <Cover large url={venue.cover_url} name={venue.name} />
        <div>
          <span className="eyebrow">ПЛОЩАДКА · {venue.city.name}</span>
          <h1>{venue.name}</h1>
          {venue.publication_status !== 'published' && (
            <p role="status">
              Предложение{' '}
              {venue.publication_status === 'rejected'
                ? 'отклонено'
                : 'ожидает принятия сообществом'}
              . <Link to="/contributions">Открыть предложения</Link>
            </p>
          )}
          {venue.address && <p>{venue.address}</p>}
          <p className="muted">
            {venue.events_count || 0} событий · {venue.followers_count || 0} подписчиков
            {venue.capacity != null ? ` · до ${venue.capacity} гостей` : ''}
          </p>
          <RatingBadge
            rating_avg={venue.rating_avg}
            ratings_count={venue.ratings_count}
            my_rating={venue.my_rating}
          />
          <div className="actions">
            {venue.publication_status === 'published' && (
              <>
                <FollowButton
                  target_type="venue"
                  target_id={id}
                  followed={venue.is_followed_by_me || false}
                />
                <FavoriteButton
                  entity_type="venue"
                  entity_id={id}
                  is_liked={venue.is_liked_by_me || false}
                />
              </>
            )}
            {user &&
              venue.publication_status === 'published' &&
              can_edit(venue.is_owner, user.level) && (
                <Link className="button" to={`/venues/${id}/edit`}>
                  Редактировать
                </Link>
              )}
          </div>
        </div>
      </div>
      <section className="panel">
        <h2>На карте</h2>
        <SceneMap
          compact
          focus={venue}
          focus_zoom={MAP_PLACE_ZOOM}
          markers={[
            {
              key: `venue:${venue.id}`,
              title: venue.name,
              lat: venue.lat,
              lng: venue.lng,
              kind: 'venue',
            },
          ]}
        />
        <Link
          className="text-button"
          to={`/map?city_id=${venue.city.id}&lat=${venue.lat}&lng=${venue.lng}&venue_id=${venue.id}`}
        >
          Открыть карту площадок →
        </Link>
      </section>
      {venue.description && (
        <section className="panel">
          <h2>О месте</h2>
          <p className="preserve-lines">{venue.description}</p>
        </section>
      )}
      <div className="actions">
        <Link className="button" to={`/events?venue_id=${id}`}>
          Афиша площадки
        </Link>
        <Link className="button" to={`/events?city_id=${venue.city.id}`}>
          Афиша города
        </Link>
        {can_create_scene(user?.level, experience) && (
          <Link className="button" to={`/events/new?venue_id=${id}`}>
            Добавить событие здесь
          </Link>
        )}
        {venue.website && /^https?:\/\//i.test(venue.website) && (
          <a className="button" href={venue.website} target="_blank" rel="noopener noreferrer">
            Сайт площадки ↗
          </a>
        )}
      </div>
      {venue.publication_status === 'published' && (
        <>
          <RatingControl
            key={`${user?.id}:${venue.my_rating}`}
            target_type="venue"
            target_id={id}
            my_rating={venue.my_rating || null}
          />
          <Reviews
            key={`${user?.id}:${id}`}
            target_type="venue"
            target_id={id}
            my_rating={venue.my_rating || null}
          />
        </>
      )}
      {can_edit_public(venue.is_owner, user?.level) && (
        <ImageUpload key={id} target_type="venue" target_id={id} />
      )}
      {venue.user_id && (
        <Link className="text-button" to={`/users/${venue.user_id}`}>
          Профиль владельца →
        </Link>
      )}
    </>
  );
}
