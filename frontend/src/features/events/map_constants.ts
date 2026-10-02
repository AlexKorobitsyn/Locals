import type { components } from '../../api/generated';

export const MAP_WORLD_CENTER: [number, number] = [20, 0];
export const MAP_WORLD_ZOOM = 2;
export const MAP_CITY_ZOOM = 12;
export const MAP_PLACE_ZOOM = 15;
export const MAP_MAX_ZOOM = 19;
export const MAP_VIEW_DELAY_MS = 350;
export const MAP_COORDINATE_PRECISION = 6;
export const MAP_MARKER_SIZE = 32;
export const MAP_FIT_PADDING = 32;
export const MAP_DEFAULT_TILE_URL = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
export const MAP_ATTRIBUTION =
  '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';
export type VenuePoint = components['schemas']['VenueRatedShort'];
export type SceneEvent = components['schemas']['EventOut'];
export type MapPoint = { lat: number; lng: number };
export type MapBounds = { min_lat: number; max_lat: number; min_lng: number; max_lng: number };
export type SceneMarker = MapPoint & {
  key: string;
  title: string;
  kind: 'venue' | 'active_venue' | 'event' | 'selected';
  count?: number;
};

export function coordinate_point(lat: string, lng: string): MapPoint | null {
  if (!lat.trim() || !lng.trim()) return null;
  const point = { lat: Number(lat), lng: Number(lng) };
  return Number.isFinite(point.lat) &&
    Math.abs(point.lat) <= 90 &&
    Number.isFinite(point.lng) &&
    Math.abs(point.lng) <= 180
    ? point
    : null;
}

export function scene_markers(venues: VenuePoint[], events: SceneEvent[]): SceneMarker[] {
  const places = new Map<number, components['schemas']['VenueShort']>(
    venues.map((venue) => [venue.id, venue]),
  );
  const counts = new Map<number, number>();
  for (const event of events) {
    if (event.venue) {
      if (!places.has(event.venue.id)) {
        places.set(event.venue.id, event.venue);
      }
      counts.set(event.venue.id, (counts.get(event.venue.id) || 0) + 1);
    }
  }
  return [
    ...Array.from(places.values(), (venue) => ({
      key: `venue:${venue.id}`,
      title: venue.name,
      lat: venue.lat,
      lng: venue.lng,
      kind: counts.has(venue.id) ? ('active_venue' as const) : ('venue' as const),
      count: counts.get(venue.id),
    })),
    ...events
      .filter((event) => !event.venue && event.lat != null && event.lng != null)
      .map((event) => ({
        key: `event:${event.id}`,
        title: event.name,
        lat: event.lat!,
        lng: event.lng!,
        kind: 'event' as const,
      })),
  ];
}
