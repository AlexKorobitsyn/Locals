import { QueryClient } from '@tanstack/react-query';
import { ApiError } from '../api/errors';
import { QUERY_RETRY_COUNT, QUERY_STALE_MS } from './constants';

export const query_client = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: QUERY_STALE_MS,
      retry: (failure_count, error) =>
        !(error instanceof ApiError && error.status < 500) && failure_count < QUERY_RETRY_COUNT,
      refetchOnWindowFocus: false,
    },
    mutations: { retry: false },
  },
});

export async function invalidate_music() {
  await query_client.invalidateQueries({
    predicate: (query) =>
      [
        'catalog',
        'detail',
        'recommendations',
        'reviews',
        'library',
        'playlist',
        'playlist_tracks',
        'catalog_picker',
        'studio',
        'following',
        'feed',
        'events',
        'venues',
        'profile',
        'me',
      ].includes(String(query.queryKey[0])),
  });
}
