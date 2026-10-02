import { Select } from './Select';
import { can_edit_public } from '../app/permissions';
import { useInfiniteQuery, useQuery } from '@tanstack/react-query';
import { api, unwrap } from '../api/client';
import type { components } from '../api/generated';
import { PAGE_LIMIT } from '../app/constants';
import { use_auth } from '../features/auth/AuthProvider';
import { ErrorState } from './States';

type EntityKind = 'artists' | 'albums' | 'venues';
type PickerItem =
  | components['schemas']['ArtistRatedShort']
  | components['schemas']['AlbumRatedShort']
  | components['schemas']['VenueRatedShort'];
export async function entity_detail(kind: EntityKind, id: number, signal?: AbortSignal) {
  if (kind === 'artists')
    return unwrap(
      await api.GET('/api/v1/artists/{artist_id}', { params: { path: { artist_id: id } }, signal }),
    );
  if (kind === 'albums')
    return unwrap(
      await api.GET('/api/v1/albums/{album_id}', { params: { path: { album_id: id } }, signal }),
    );
  return unwrap(
    await api.GET('/api/v1/venues/{venue_id}', { params: { path: { venue_id: id } }, signal }),
  );
}

export function EntityPicker({
  kind,
  label,
  value,
  on_change,
  required = false,
  owner_only = false,
  disabled = false,
}: {
  kind: EntityKind;
  label: string;
  value: number | null;
  on_change: (value: number | null) => void;
  required?: boolean;
  owner_only?: boolean;
  disabled?: boolean;
}) {
  const { user } = use_auth();
  const query = useInfiniteQuery({
    queryKey: ['catalog_picker', user?.id, kind, owner_only ? 'owned' : 'all'],
    initialPageParam: 0,
    queryFn: async ({ pageParam: offset, signal }) => {
      const options = { params: { query: { limit: PAGE_LIMIT, offset } }, signal };
      if (kind === 'artists')
        return owner_only
          ? unwrap(await api.GET('/api/v1/me/artists', options))
          : unwrap(await api.GET('/api/v1/artists', options));
      if (kind === 'albums')
        return owner_only
          ? unwrap(await api.GET('/api/v1/me/albums', options))
          : unwrap(await api.GET('/api/v1/albums', options));
      return unwrap(await api.GET('/api/v1/venues', options));
    },
    getNextPageParam: (page) =>
      page.items.length && page.offset + page.items.length < page.total
        ? page.offset + page.items.length
        : undefined,
  });
  const selected = useQuery({
    queryKey: ['catalog_picker', user?.id, kind, value],
    enabled: !!value,
    queryFn: ({ signal }) => entity_detail(kind, value!, signal),
  });
  const items = query.data?.pages.flatMap<PickerItem>((page) => page.items) || [];
  const selected_name =
    selected.data && ('name' in selected.data ? selected.data.name : selected.data.title);
  return (
    <div className="picker-field">
      <label>
        {label}
        <Select
          label={label}
          value={value || ''}
          on_change={(next_value) => on_change(Number(next_value) || null)}
          required={required}
          disabled={disabled || query.isPending}
        >
          <option value="">{required ? 'Выберите' : 'Не указано'}</option>
          {value && !items.some((item) => item.id === value) && (
            <option value={value}>{selected_name || 'Загрузка выбранной записи…'}</option>
          )}
          {items.map((item) => (
            <option key={item.id} value={item.id}>
              {'name' in item ? item.name : item.title}
            </option>
          ))}
        </Select>
      </label>
      {query.hasNextPage && (
        <button
          type="button"
          className="text-button"
          disabled={query.isFetchingNextPage || disabled}
          onClick={() => void query.fetchNextPage()}
        >
          Показать ещё
        </button>
      )}
      {owner_only && value && selected.isPending && (
        <small role="status">Проверяем выбранную запись…</small>
      )}
      {owner_only && selected.data && !can_edit_public(selected.data.is_owner, user?.level) && (
        <p className="field-error" role="alert">
          Выберите своего артиста или релиз. Публиковать от имени другого автора нельзя.
        </p>
      )}
      {(query.isError || selected.isError) && (
        <ErrorState
          error={query.error || selected.error}
          retry={() => {
            void query.refetch();
            if (value) void selected.refetch();
          }}
        />
      )}
    </div>
  );
}
