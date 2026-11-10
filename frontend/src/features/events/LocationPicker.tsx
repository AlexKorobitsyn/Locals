import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api, unwrap } from '../../api/client';
import { ErrorState } from '../../components/States';
import { use_auth } from '../auth/AuthProvider';
import { SceneMap } from './SceneMap';
import {
  MAP_COORDINATE_PRECISION,
  MAP_PLACE_ZOOM,
  coordinate_point,
  type MapBounds,
  type MapPoint,
  type SceneMarker,
} from './map_constants';
import { use_map_city, use_map_venues } from './map_queries';

export function LocationPicker({
  venues,
  city_id,
  venue_id,
  lat,
  lng,
  on_point,
  on_venue,
}: {
  venues: boolean;
  city_id: number | null;
  venue_id: number | null;
  lat: string;
  lng: string;
  on_point: (point: MapPoint) => void;
  on_venue: (id: number | null) => void;
}) {
  const { user } = use_auth();
  const [bounds, set_bounds] = useState<MapBounds | null>(null);
  const places = use_map_venues(bounds, city_id);
  const city = use_map_city(city_id);
  const chosen = useQuery({
    queryKey: ['catalog_picker', user?.id, 'venues', venue_id],
    enabled: !venues && !!venue_id,
    queryFn: async ({ signal }) =>
      unwrap(
        await api.GET('/api/v1/venues/{venue_id}', {
          params: { path: { venue_id: venue_id! } },
          signal,
        }),
      ),
  });
  const point = !venues && venue_id ? chosen.data || null : coordinate_point(lat, lng);
  const available = places.data?.pages.flatMap((page) => page.items) || [];
  const markers: SceneMarker[] = available
    .filter((venue) => venues || venue.id !== venue_id)
    .map((venue) => ({
      key: `venue:${venue.id}`,
      title: venue.name,
      lat: venue.lat,
      lng: venue.lng,
      kind: 'venue',
    }));
  if (point)
    markers.push({
      ...point,
      key: 'selected',
      title:
        chosen.data && !venues && venue_id ? `Выбрано: ${chosen.data.name}` : 'Выбранное место',
      kind: 'selected',
    });
  return (
    <div className="location-picker">
      <h2>Место на карте</h2>
      <p className="muted">
        {venues
          ? 'Нажмите на карту, чтобы поставить метку площадки. Координаты и адрес заполнятся автоматически.'
          : 'Нажмите метку площадки, чтобы привязать событие. Нажатие на свободное место задаёт точку события без площадки.'}
      </p>
      <SceneMap
        compact
        label={venues ? 'Выбор места площадки' : 'Выбор площадки или места события'}
        markers={markers}
        focus={point || city.data}
        focus_zoom={point ? MAP_PLACE_ZOOM : undefined}
        auto_fit
        on_view={set_bounds}
        on_point={on_point}
        on_select={(key) => {
          const venue = available.find((place) => key === `venue:${place.id}`);
          if (!venue) return;
          if (venues) on_point(venue);
          else on_venue(venue.id);
        }}
      />
      {chosen.data && !venues && venue_id ? (
        <div className="map-summary">
          <span>
            Площадка: <strong>{chosen.data.name}</strong> · {chosen.data.city.name}. Место события
            берётся из площадки.
          </span>
          <button type="button" className="text-button" onClick={() => on_venue(null)}>
            Отвязать площадку
          </button>
        </div>
      ) : (
        point && (
          <small className="muted">
            Выбранная точка: {point.lat.toFixed(MAP_COORDINATE_PRECISION)},{' '}
            {point.lng.toFixed(MAP_COORDINATE_PRECISION)}
          </small>
        )
      )}
      {places.hasNextPage && (
        <button
          type="button"
          className="text-button"
          disabled={places.isFetchingNextPage}
          onClick={() => void places.fetchNextPage()}
        >
          Ещё площадки в этой области
        </button>
      )}
      {places.isError && <ErrorState error={places.error} retry={() => void places.refetch()} />}
      {chosen.isError && <ErrorState error={chosen.error} retry={() => void chosen.refetch()} />}
      {city.isError && <ErrorState error={city.error} retry={() => void city.refetch()} />}
    </div>
  );
}
