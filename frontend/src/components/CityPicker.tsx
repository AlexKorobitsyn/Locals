import { useEffect, useId, useRef, useState, type KeyboardEvent } from 'react';
import { useInfiniteQuery, useQuery, useQueryClient } from '@tanstack/react-query';
import { X } from 'lucide-react';
import { api, unwrap } from '../api/client';
import type { components } from '../api/generated';
import { CITY_SEARCH_DELAY_MS, PAGE_LIMIT } from '../app/constants';

type City = components['schemas']['CityOut'];

function city_label(city: { name: string; region?: string | null }) {
  return city.region && city.region !== city.name ? `${city.name} · ${city.region}` : city.name;
}

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
  const id = useId();
  const input = useRef<HTMLInputElement>(null);
  const client = useQueryClient();
  const [draft, set_draft] = useState<string | null>(null);
  const [query_text, set_query_text] = useState('');
  const [open, set_open] = useState(false);
  const [active, set_active] = useState(-1);
  const [invalid, set_invalid] = useState(false);
  const selected = useQuery({
    queryKey: ['cities', 'detail', value],
    enabled: !!value,
    queryFn: async ({ signal }) =>
      unwrap(
        await api.GET('/api/v1/cities/{city_id}', {
          params: { path: { city_id: value! } },
          signal,
        }),
      ),
  });
  const selected_label = value
    ? selected.data
      ? city_label(selected.data)
      : initial_name || ''
    : '';
  const text = draft ?? selected_label;
  const search = draft?.trim() || '';
  useEffect(() => {
    const timeout = window.setTimeout(() => set_query_text(search), CITY_SEARCH_DELAY_MS);
    return () => window.clearTimeout(timeout);
  }, [search]);
  useEffect(() => {
    if (value) set_draft(null);
  }, [value]);
  useEffect(() => {
    input.current?.setCustomValidity(required && !value ? 'Выберите город из подсказок.' : '');
  }, [required, value]);
  const query = useInfiniteQuery({
    queryKey: ['cities', 'search', query_text],
    enabled: open,
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
  const matches_search = search === query_text;
  const items = matches_search ? query.data?.pages.flatMap((page) => page.items) || [] : [];
  const loading = !matches_search || query.isPending;
  useEffect(() => {
    if (open && active >= 0)
      document.getElementById(`${id}-option-${active}`)?.scrollIntoView?.({ block: 'nearest' });
  }, [open, active, id]);

  function choose(city: City) {
    client.setQueryData(['cities', 'detail', city.id], city);
    set_draft(null);
    set_open(false);
    set_active(-1);
    set_invalid(false);
    on_change(city.id);
  }
  function clear() {
    set_draft(null);
    set_query_text('');
    set_active(-1);
    set_invalid(false);
    on_change(null);
    input.current?.focus();
  }
  function key_down(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      event.preventDefault();
      set_open(true);
      if (items.length)
        set_active((current) =>
          event.key === 'ArrowDown'
            ? Math.min(current + 1, items.length - 1)
            : current < 0
              ? items.length - 1
              : Math.max(0, current - 1),
        );
    } else if (event.key === 'Enter' && open) {
      event.preventDefault();
      const city = items[active >= 0 ? active : 0];
      if (city) choose(city);
    } else if (event.key === 'Escape') {
      event.preventDefault();
      set_open(false);
      set_active(-1);
    }
  }
  return (
    <div
      className={`picker-field city-autocomplete${open ? ' is-open' : ''}`}
      onBlur={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget as Node | null)) set_open(false);
      }}
    >
      <label htmlFor={id}>Город</label>
      <div className="city-input-wrap">
        <input
          ref={input}
          id={id}
          type="text"
          role="combobox"
          autoComplete="off"
          value={text}
          required={required}
          placeholder={
            required ? 'Введите название города' : 'Все города · начните вводить название'
          }
          aria-autocomplete="list"
          aria-expanded={open}
          aria-controls={open ? `${id}-list` : undefined}
          aria-activedescendant={open && items[active] ? `${id}-option-${active}` : undefined}
          aria-invalid={invalid || undefined}
          aria-describedby={invalid ? `${id}-error` : undefined}
          onFocus={() => set_open(true)}
          onClick={() => set_open(true)}
          onChange={(event) => {
            set_draft(event.target.value);
            set_open(true);
            set_active(-1);
            set_invalid(false);
            if (value) on_change(null);
          }}
          onInvalid={() => {
            set_invalid(true);
            set_open(true);
          }}
          onKeyDown={key_down}
        />
        {(text || value) && (
          <button
            type="button"
            className="city-clear"
            aria-label="Очистить город"
            onMouseDown={(event) => event.preventDefault()}
            onClick={clear}
          >
            <X size={16} />
          </button>
        )}
        {open && (
          <div className="city-suggestions" onMouseDown={(event) => event.preventDefault()}>
            <div
              id={`${id}-list`}
              role="listbox"
              aria-label="Подсказки городов"
              aria-busy={loading}
            >
              {items.map((city, index) => (
                <div
                  id={`${id}-option-${index}`}
                  key={city.id}
                  role="option"
                  aria-label={city_label(city)}
                  aria-selected={value === city.id}
                  className={`city-option${active === index ? ' active' : ''}`}
                  onPointerMove={() => set_active(index)}
                  onClick={() => choose(city)}
                >
                  <strong>{city.name}</strong>
                  <small>
                    {[city.region !== city.name && city.region, city.country]
                      .filter(Boolean)
                      .join(' · ')}
                  </small>
                </div>
              ))}
            </div>
            {loading ? (
              <p className="city-hint" role="status">
                Ищем города…
              </p>
            ) : query.isError ? (
              <div className="city-hint" role="alert">
                Не удалось загрузить города.{' '}
                <button type="button" className="text-button" onClick={() => void query.refetch()}>
                  Повторить
                </button>
              </div>
            ) : !items.length ? (
              <p className="city-hint" role="status">
                Город не найден. Попробуйте другое название.
              </p>
            ) : null}
            {matches_search && query.hasNextPage && (
              <button
                type="button"
                className="text-button city-more"
                disabled={query.isFetchingNextPage}
                onClick={() => void query.fetchNextPage()}
              >
                {query.isFetchingNextPage ? 'Загружаем…' : 'Ещё города'}
              </button>
            )}
          </div>
        )}
      </div>
      {invalid && (
        <small id={`${id}-error`} className="field-error">
          Выберите город из подсказок.
        </small>
      )}
      {!open && !value && draft?.trim() && !invalid && (
        <small className="muted">Выберите город из подсказок, чтобы применить его.</small>
      )}
      {selected.isError && value && (
        <small className="field-error">
          Не удалось загрузить выбранный город.{' '}
          <button type="button" className="text-button" onClick={() => void selected.refetch()}>
            Повторить
          </button>
        </small>
      )}
      <small className="muted city-attribution">
        Справочник:{' '}
        <a href="https://www.geonames.org/" target="_blank" rel="noreferrer">
          GeoNames
        </a>
      </small>
    </div>
  );
}
