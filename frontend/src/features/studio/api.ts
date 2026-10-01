import { api, unwrap } from '../../api/client';
import type { CatalogKind } from '../../api/catalog';
import { PAGE_LIMIT } from '../../app/constants';

export async function studio_page(
  kind: CatalogKind,
  offset = 0,
  sort = '-created_at',
  signal?: AbortSignal,
) {
  const options = { params: { query: { limit: PAGE_LIMIT, offset, sort } }, signal };
  if (kind === 'artists') return unwrap(await api.GET('/api/v1/me/artists', options));
  if (kind === 'albums') return unwrap(await api.GET('/api/v1/me/albums', options));
  return unwrap(await api.GET('/api/v1/me/tracks', options));
}
