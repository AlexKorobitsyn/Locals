import { useEffect, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router';
import * as L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import {
  MAP_ATTRIBUTION,
  MAP_CITY_ZOOM,
  MAP_DEFAULT_TILE_URL,
  MAP_FIT_PADDING,
  MAP_MARKER_SIZE,
  MAP_MAX_ZOOM,
  MAP_VIEW_DELAY_MS,
  MAP_WORLD_CENTER,
  MAP_WORLD_ZOOM,
  type MapBounds,
  type MapPoint,
  type SceneMarker,
} from './map_constants';

export function SceneMap({
  markers,
  focus,
  focus_zoom = MAP_CITY_ZOOM,
  on_select,
  on_point,
  on_view,
  auto_fit = false,
  label = 'Карта площадок и событий',
  compact = false,
  popup_links = false,
}: {
  markers: SceneMarker[];
  focus?: MapPoint | null;
  focus_zoom?: number;
  on_select?: (key: string) => void;
  on_point?: (point: MapPoint) => void;
  on_view?: (bounds: MapBounds) => void;
  auto_fit?: boolean;
  label?: string;
  compact?: boolean;
  popup_links?: boolean;
}) {
  const navigate = useNavigate();
  const element = useRef<HTMLDivElement>(null);
  const map_ref = useRef<L.Map | null>(null);
  const callbacks = useRef({ on_select, on_point, on_view });
  const fitted = useRef(false);
  const marker_key = JSON.stringify(markers);
  const [tiles_failed, set_tiles_failed] = useState(false);
  const config = useQuery({
    queryKey: ['map_config'],
    queryFn: async ({ signal }) => {
      const response = await fetch('/config.json', { signal, cache: 'no-store' });
      if (!response.ok) throw new Error('Map configuration unavailable');
      return response.json() as Promise<{ map_tile_url?: string }>;
    },
  });
  useEffect(() => {
    callbacks.current = { on_select, on_point, on_view };
  });
  useEffect(() => {
    if (!element.current) return;
    const map = L.map(element.current, {
      center: MAP_WORLD_CENTER,
      zoom: MAP_WORLD_ZOOM,
      minZoom: MAP_WORLD_ZOOM,
      maxZoom: MAP_MAX_ZOOM,
      scrollWheelZoom: false,
      worldCopyJump: true,
    });
    map_ref.current = map;
    let timer: ReturnType<typeof setTimeout>;
    const report = () => {
      const bounds = map.getBounds();
      callbacks.current.on_view?.({
        min_lat: Math.max(-90, bounds.getSouth()),
        max_lat: Math.min(90, bounds.getNorth()),
        min_lng: Math.min(180, Math.max(-180, bounds.getWest())),
        max_lng: Math.min(180, Math.max(-180, bounds.getEast())),
      });
    };
    map.on('moveend', () => {
      clearTimeout(timer);
      timer = setTimeout(report, MAP_VIEW_DELAY_MS);
    });
    map.on('click', (event: L.LeafletMouseEvent) => {
      const point = event.latlng.wrap();
      callbacks.current.on_point?.({ lat: point.lat, lng: point.lng });
    });
    const resize = new ResizeObserver(() => map.invalidateSize());
    resize.observe(element.current);
    report();
    return () => {
      clearTimeout(timer);
      resize.disconnect();
      map.remove();
      map_ref.current = null;
      fitted.current = false;
    };
  }, []);
  useEffect(() => {
    const map = map_ref.current;
    if (!map || config.isPending) return;
    const layer = L.tileLayer(config.data?.map_tile_url || MAP_DEFAULT_TILE_URL, {
      attribution: MAP_ATTRIBUTION,
      maxZoom: MAP_MAX_ZOOM,
      noWrap: true,
    });
    layer.on('tileerror', () => set_tiles_failed(true));
    layer.on('tileload', () => set_tiles_failed(false));
    layer.addTo(map);
    return () => {
      layer.remove();
    };
  }, [config.data?.map_tile_url, config.isPending]);
  useEffect(() => {
    if (focus) map_ref.current?.setView([focus.lat, focus.lng], focus_zoom, { animate: false });
  }, [focus?.lat, focus?.lng, focus_zoom]);
  useEffect(() => {
    const map = map_ref.current;
    if (!map) return;
    const group = L.layerGroup().addTo(map);
    const points: SceneMarker[] = JSON.parse(marker_key);
    for (const point of points) {
      const label = point.count ? `${point.title} · ${point.count} событий` : point.title;
      const badge = document.createElement('span');
      badge.textContent = point.count ? String(point.count) : point.kind === 'event' ? '♪' : '●';
      const marker = L.marker([point.lat, point.lng], {
        icon: L.divIcon({
          html: badge,
          className: `scene-marker scene-marker-${point.kind}`,
          iconSize: [MAP_MARKER_SIZE, MAP_MARKER_SIZE],
          iconAnchor: [MAP_MARKER_SIZE / 2, MAP_MARKER_SIZE / 2],
        }),
        title: label,
        bubblingMouseEvents: false,
      }).addTo(group);
      marker.getElement()?.setAttribute('aria-label', label);
      const tooltip = document.createElement('span');
      tooltip.textContent = label;
      marker.bindTooltip(tooltip);
      const popup = document.createElement('div');
      const title = document.createElement('strong');
      title.textContent = label;
      popup.append(title);
      if (popup_links && /^(venue|event):[1-9]\d*$/.test(point.key)) {
        const [kind, id] = point.key.split(':');
        const link = document.createElement('a');
        link.href = `/${kind === 'venue' ? 'venues' : 'events'}/${id}`;
        link.textContent = kind === 'venue' ? 'Открыть площадку →' : 'Открыть событие →';
        link.addEventListener('click', (event) => {
          event.preventDefault();
          void navigate(link.getAttribute('href')!);
        });
        popup.append(document.createElement('br'), link);
      }
      marker.bindPopup(popup);
      marker.on('click', () => callbacks.current.on_select?.(point.key));
    }
    if (auto_fit && !focus && !fitted.current && points.length) {
      fitted.current = true;
      map.fitBounds(L.latLngBounds(points.map((point) => [point.lat, point.lng])), {
        padding: [MAP_FIT_PADDING, MAP_FIT_PADDING],
        maxZoom: MAP_CITY_ZOOM,
        animate: false,
      });
    }
    return () => {
      group.remove();
    };
  }, [marker_key, auto_fit, focus?.lat, focus?.lng, popup_links, navigate]);
  return (
    <div className={`scene-map-wrap ${compact ? 'scene-map-compact' : ''}`}>
      <div
        ref={element}
        className="scene-map"
        role="region"
        aria-label={label}
        data-testid="scene-map"
      />
      {tiles_failed && (
        <p className="map-notice" role="status">
          Подложка карты недоступна. Метки и выбор места продолжают работать.
        </p>
      )}
    </div>
  );
}
