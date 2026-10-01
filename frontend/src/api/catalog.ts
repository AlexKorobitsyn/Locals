import { api, unwrap } from './client';
import type { components } from './generated';
import { MAX_PAGE_LIMIT, PAGE_LIMIT } from '../app/constants';

export type CatalogKind = 'tracks' | 'albums' | 'artists';
export type Track = components['schemas']['TrackRatedShort'];
export type RatingTarget = components['schemas']['RatingTarget'];
export type CatalogFilters = { artist_id?: number; album_id?: number };

export async function catalog_page(
  kind: CatalogKind,
  offset = 0,
  sort = '-created_at',
  filters: CatalogFilters = {},
  signal?: AbortSignal,
) {
  const query = { limit: PAGE_LIMIT, offset, sort, ...filters };
  if (kind === 'artists')
    return unwrap(await api.GET('/api/v1/artists', { params: { query }, signal }));
  if (kind === 'albums')
    return unwrap(await api.GET('/api/v1/albums', { params: { query }, signal }));
  return unwrap(await api.GET('/api/v1/tracks', { params: { query }, signal }));
}

export async function all_genres(signal?: AbortSignal) {
  const items: components['schemas']['GenreOut'][] = [];
  let offset = 0;
  do {
    const page = unwrap(
      await api.GET('/api/v1/genres', {
        params: { query: { limit: MAX_PAGE_LIMIT, offset } },
        signal,
      }),
    );
    items.push(...page.items);
    if (!page.items.length || items.length >= page.total) break;
    offset += page.items.length;
  } while (!signal?.aborted);
  return items;
}
