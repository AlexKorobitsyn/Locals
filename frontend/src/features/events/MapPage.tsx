import { Select } from '../../components/Select';
import { useEffect, useState } from 'react';
import { useInfiniteQuery } from '@tanstack/react-query';
import { Link, useSearchParams } from 'react-router';
import { MapPin, CalendarDays } from 'lucide-react';
import { api, unwrap } from '../../api/client';
import { MAX_PAGE_LIMIT, format_datetime, parse_id } from '../../app/constants';
import { CityPicker } from '../../components/CityPicker';
import { ErrorState } from '../../components/States';
import { use_auth } from '../auth/AuthProvider';
import { use_event_types } from './EventPages';
import { SceneMap } from './SceneMap';
import { coordinate_point, scene_markers, type MapBounds } from './map_constants';
import { use_map_city, use_map_venues } from './map_queries';

export function MapPage() {
  const { user } = use_auth();
  const [search, set_search] = useSearchParams();
  const [bounds, set_bounds] = useState<MapBounds | null>(null);
  const [selected, set_selected] = useState<string | null>(() => {
    const venue = parse_id(search.get('venue_id') || undefined);
    const event = parse_id(search.get('event_id') || undefined);
    return venue ? `venue:${venue}` : event ? `event:${event}` : null;
  });
  const [now] = useState(() => new Date().toISOString());
  const city_id = parse_id(search.get('city_id') || undefined);
  const layer = search.get('layer');
  const [show_events, set_show_events] = useState(layer !== 'venues');
  useEffect(() => {
    set_show_events(layer !== 'venues');
  }, [layer]);
  const city = use_map_city(city_id);
  const venues = use_map_venues(bounds, city_id);
  const types = use_event_types();
  const from = search.get('starts_after');
  const until = search.get('starts_before');
  const valid_date = (value: string | null) =>
    value && Number.isFinite(new Date(value).getTime()) ? new Date(value).toISOString() : undefined;
  const starts_after = valid_date(from) || now;
  const starts_before = valid_date(until);
  const date_error =
    (!!from && !valid_date(from)) ||
    (!!until && !starts_before) ||
    (!!starts_before && starts_before <= starts_after);
  const events = useInfiniteQuery({
    queryKey: [
      'events',
      'map',
      user?.id,
      bounds,
      city_id,
      starts_after,
      starts_before,
      search.get('type_event_id'),
    ],
    enabled: !!bounds && show_events && !date_error,
    initialPageParam: 0,
    queryFn: async ({ signal, pageParam }) =>
      unwrap(
        await api.GET('/api/v1/events', {
          params: {
            query: {
              ...bounds!,
              city_id: city_id || undefined,
              starts_after,
              starts_before,
              type_event_id: parse_id(search.get('type_event_id') || undefined) || undefined,
              limit: MAX_PAGE_LIMIT,
              offset: pageParam,
              sort: 'starts_at',
            },
          },
          signal,
        }),
      ),
    getNextPageParam: (page) =>
      page.items.length && page.offset + page.items.length < page.total
        ? page.offset + page.items.length
        : undefined,
  });
  const venue_items = venues.data?.pages.flatMap((page) => page.items) || [];
  const event_items =
    show_events && !date_error ? events.data?.pages.flatMap((page) => page.items) || [] : [];
  const markers = scene_markers(venue_items, event_items);
  const selected_venue =
    venue_items.find((venue) => selected === `venue:${venue.id}`) ||
    event_items.find((event) => selected === `venue:${event.venue?.id}`)?.venue;
  const selected_events = selected_venue
    ? event_items.filter((event) => event.venue?.id === selected_venue.id)
    : event_items.filter((event) => selected === `event:${event.id}`);
  const focus = coordinate_point(search.get('lat') || '', search.get('lng') || '') || city.data;
  function change(key: string, value: string) {
    set_search((previous) => {
      const next = new URLSearchParams(previous);
      if (value) next.set(key, value);
      else next.delete(key);
      if (key === 'city_id') {
        for (const parameter of ['lat', 'lng', 'venue_id', 'event_id']) next.delete(parameter);
        set_selected(null);
      }
      return next;
    });
  }
  return (
    <>
      <div className="section-heading">
        <div className="page-intro">
          <span className="eyebrow">МУЗЫКА РЯДОМ</span>
          <h1>
            Карта сцены<span className="heading-dot">.</span>
          </h1>
          <p className="muted">
            Площадки видны сразу. Выберите место, чтобы увидеть афишу или добавить событие.
          </p>
        </div>
        <div className="actions">
          <Link className="button" to="/venues">
            Список площадок
          </Link>
          <Link className="button" to="/events">
            Список событий
          </Link>
        </div>
      </div>
      <div className="panel form scene-filters">
        <CityPicker value={city_id} on_change={(id) => change('city_id', id ? String(id) : '')} />
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={show_events}
            onChange={(event) => {
              set_show_events(event.target.checked);
              change('layer', event.target.checked ? 'events' : 'venues');
            }}
          />
          Показывать события
        </label>
        {show_events && (
          <>
            <label>
              С даты
              <input
                type="datetime-local"
                value={from || ''}
                onChange={(event) => change('starts_after', event.target.value)}
              />
            </label>
            <label>
              До даты
              <input
                type="datetime-local"
                value={until || ''}
                onChange={(event) => change('starts_before', event.target.value)}
              />
            </label>
            <label>
              Тип события
              <Select
                label="Тип события"
                value={search.get('type_event_id') || ''}
                on_change={(next_value) => change('type_event_id', next_value)}
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
              По умолчанию — предстоящие события. Время:{' '}
              {Intl.DateTimeFormat().resolvedOptions().timeZone}.
            </small>
          </>
        )}
        <button
          className="text-button"
          onClick={() => {
            set_search({});
            set_selected(null);
          }}
        >
          Сбросить фильтры
        </button>
      </div>
      {date_error && (
        <p className="field-error" role="alert">
          Конец периода должен быть позже начала.
        </p>
      )}
      <div className="map-legend">
        <span>
          <i className="legend-venue" />
          Площадка
        </span>
        <span>
          <i className="legend-active" />
          Площадка с событиями
        </span>
        <span>
          <i className="legend-event" />
          Событие без площадки
        </span>
      </div>
      <SceneMap
        markers={markers}
        focus={focus}
        auto_fit
        popup_links
        on_view={set_bounds}
        on_select={set_selected}
      />
      <div className="map-summary" aria-live="polite">
        {venues.isFetching || (show_events && events.isFetching) ? (
          <span role="status">Обновляем карту…</span>
        ) : (
          <span>
            В области карты: {venue_items.length} из {venues.data?.pages[0]?.total || 0} площадок
            {show_events &&
              ` · ${event_items.length} из ${events.data?.pages[0]?.total || 0} событий`}
          </span>
        )}
        {venues.hasNextPage && (
          <button
            className="button"
            disabled={venues.isFetchingNextPage}
            onClick={() => void venues.fetchNextPage()}
          >
            Загрузить ещё площадки
          </button>
        )}
        {show_events && events.hasNextPage && (
          <button
            className="button"
            disabled={events.isFetchingNextPage}
            onClick={() => void events.fetchNextPage()}
          >
            Загрузить ещё события
          </button>
        )}
      </div>
      {venues.isError && <ErrorState error={venues.error} retry={() => void venues.refetch()} />}
      {show_events && events.isError && (
        <ErrorState error={events.error} retry={() => void events.refetch()} />
      )}
      {city.isError && <ErrorState error={city.error} retry={() => void city.refetch()} />}
      {show_events && types.isError && (
        <ErrorState error={types.error} retry={() => void types.refetch()} />
      )}
      <section className="panel map-selection" aria-label="Выбранное место">
        {selected_venue ? (
          <>
            <span className="eyebrow">ПЛОЩАДКА</span>
            <h2>
              <Link to={`/venues/${selected_venue.id}`}>{selected_venue.name}</Link>
            </h2>
            <p>
              <MapPin size={16} /> {selected_venue.city.name}
            </p>
            <div className="actions">
              <Link className="button" to={`/events?venue_id=${selected_venue.id}`}>
                Афиша площадки
              </Link>
              {user && (
                <Link className="button primary" to={`/events/new?venue_id=${selected_venue.id}`}>
                  Добавить событие здесь
                </Link>
              )}
            </div>
            {show_events && !selected_events.length && (
              <p className="muted">В загруженной части афиши нет событий за выбранный период.</p>
            )}
          </>
        ) : (
          !selected_events.length && (
            <p className="muted">Нажмите метку площадки или события на карте.</p>
          )
        )}
        {selected_events.map((event) => (
          <article key={event.id} className="map-event">
            <h3>
              <Link to={`/events/${event.id}`}>{event.name}</Link>
            </h3>
            <p>
              <CalendarDays size={16} />
              {format_datetime(event.starts_at)}
            </p>
          </article>
        ))}
      </section>
      {user && (
        <div className="actions">
          <Link className="button" to="/venues/new">
            Добавить площадку
          </Link>
          <Link className="button" to="/events/new">
            Добавить событие
          </Link>
        </div>
      )}
    </>
  );
}
