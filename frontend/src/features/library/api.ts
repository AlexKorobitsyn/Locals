import { api, unwrap } from '../../api/client';
import type { components } from '../../api/generated';
import { MAX_PAGE_LIMIT } from '../../app/constants';

export async function all_own_playlists(signal?: AbortSignal) {
  const items: components['schemas']['PlaylistShort'][] = [];
  let offset = 0;
  while (true) {
    const page = unwrap(
      await api.GET('/api/v1/me/playlists', {
        params: { query: { limit: MAX_PAGE_LIMIT, offset } },
        signal,
      }),
    );
    items.push(...page.items);
    if (!page.items.length || items.length >= page.total) return items;
    offset += page.items.length;
  }
}

export async function all_playlist_tracks(playlist_id: number, signal?: AbortSignal) {
  const items: components['schemas']['PlaylistTrackItem'][] = [];
  let offset = 0;
  while (true) {
    const page = unwrap(
      await api.GET('/api/v1/playlists/{playlist_id}/tracks', {
        params: { path: { playlist_id }, query: { limit: MAX_PAGE_LIMIT, offset } },
        signal,
      }),
    );
    items.push(...page.items);
    if (!page.items.length || items.length >= page.total) return { ...page, items };
    offset += page.items.length;
  }
}
