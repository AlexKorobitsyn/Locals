import { Select } from './Select';
import { useEffect, useState } from 'react';
import { useInfiniteQuery } from '@tanstack/react-query';
import { api, unwrap } from '../api/client';
import { CITY_SEARCH_DELAY_MS, PAGE_LIMIT } from '../app/constants';
import { ErrorState } from './States';

export function CityPicker({
  value,
  on_change,
  initial_name,
  required = false,
}: {
  value: number | null;
  on_change: (value: number | null) => void;
  initial_name?: string;
  required?: boolean;
}) {
  const [search, set_search] = useState('');
  const [query_text, set_query_text] = useState('');
  const [selected_name, set_selected_name] = useState(initial_name || 'Выбранный город');
  useEffect(() => {
    const timeout = window.setTimeout(() => set_query_text(search.trim()), CITY_SEARCH_DELAY_MS);
    return () => window.clearTimeout(timeout);
  }, [search]);
  const query = useInfiniteQuery({
    queryKey: ['cities', query_text],
    initialPageParam: 0,
    queryFn: async ({ pageParam: offset, signal }) =>
      unwrap(
        await api.GET('/api/v1/cities', {
          params: { query: { q: query_text || undefined, limit: PAGE_LIMIT, offset } },
          signal,
        }),
      ),
    getNextPageParam: (page) =>
      page.items.length && page.offset + page.items.length < page.total
        ? page.offset + page.items.length
        : undefined,
  });
  const items = query.data?.pages.flatMap((page) => page.items) || [];
  return (
    <div className="picker-field">
      <label>
        Поиск города
        <input
          type="search"
          value={search}
          onChange={(event) => set_search(event.target.value)}
          placeholder="Название города"
        />
      </label>
      <label>
        Город
        <Select
          label="Город"
          value={value || ''}
          required={required}
          disabled={query.isPending}
          on_change={(next_value) => {
            on_change(Number(next_value) || null);
            const city = items.find((item) => String(item.id) === next_value);
            set_selected_name(city ? `${city.name}${city.region ? ` · ${city.region}` : ''}` : '');
          }}
        >
          <option value="">{required ? 'Выберите город' : 'Все города / не указан'}</option>
          {value && !items.some((item) => item.id === value) && (
            <option value={value}>{selected_name}</option>
          )}
          {items.map((city) => (
            <option key={city.id} value={city.id}>
              {city.name}
              {city.region ? ` · ${city.region}` : ''}
            </option>
          ))}
        </Select>
      </label>
      {query.hasNextPage && (
        <button
          className="text-button"
          type="button"
          disabled={query.isFetchingNextPage}
          onClick={() => void query.fetchNextPage()}
        >
          Ещё города
        </button>
      )}
      {query.isError && <ErrorState error={query.error} retry={() => void query.refetch()} />}
      {!query.isPending && !items.length && (
        <small className="muted">Город не найден. Попробуйте другое название.</small>
      )}
    </div>
  );
}
