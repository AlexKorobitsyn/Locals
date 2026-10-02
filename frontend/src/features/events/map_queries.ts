import { useInfiniteQuery, useQuery } from '@tanstack/react-query';
import { api, unwrap } from '../../api/client';
import { MAX_PAGE_LIMIT } from '../../app/constants';
import { use_auth } from '../auth/AuthProvider';
import type { MapBounds } from './map_constants';

export function use_map_venues(bounds: MapBounds | null, city_id?: number | null) {
  const { user } = use_auth();
  return useInfiniteQuery({
    queryKey: ['venues', 'map', user?.id, bounds, city_id],
    enabled: !!bounds,
    initialPageParam: 0,
    queryFn: async ({ signal, pageParam }) =>
      unwrap(
        await api.GET('/api/v1/venues', {
          params: {
            query: {
              ...bounds!,
              city_id: city_id || undefined,
              limit: MAX_PAGE_LIMIT,
              offset: pageParam,
              sort: 'id',
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
}

export function use_map_city(city_id: number | null) {
  return useQuery({
    queryKey: ['cities', 'detail', city_id],
    enabled: !!city_id,
    queryFn: async ({ signal }) =>
      unwrap(
        await api.GET('/api/v1/cities/{city_id}', {
          params: { path: { city_id: city_id! } },
          signal,
        }),
      ),
  });
}
