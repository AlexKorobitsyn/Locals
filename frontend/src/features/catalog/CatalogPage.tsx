import { useState } from 'react';
import { Link, useSearchParams } from 'react-router';
import { useQuery } from '@tanstack/react-query';
import { ArrowUpRight, ListPlus, Play } from 'lucide-react';
import { catalog_page, type CatalogFilters, type CatalogKind } from '../../api/catalog';
import type { components } from '../../api/generated';
import { format_duration, PAGE_LIMIT } from '../../app/constants';
import { Cover } from '../../components/Cover';
import { EmptyState, ErrorState, LoadingState } from '../../components/States';
import { Pagination } from '../../components/Pagination';
import { use_auth } from '../auth/AuthProvider';
import { use_player } from '../player/PlayerProvider';
import { RatingBadge } from '../ratings/RatingControl';

type CatalogItem =
  | components['schemas']['TrackRatedShort']
  | components['schemas']['AlbumRatedShort']
  | components['schemas']['ArtistRatedShort'];
const TITLES: Record<CatalogKind, string> = {
  tracks: 'Треки',
  albums: 'Альбомы',
  artists: 'Артисты',
};
const SUBTITLES: Record<CatalogKind, string> = {
  tracks: 'Слушайте внимательно. Оценивайте честно. Находите своё.',
  albums: 'От первого трека до последнего. Музыка целиком.',
  artists: 'Люди и группы, за которыми стоит звук.',
};
const COMMON_SORTS = [
  { value: '-created_at', label: 'Сначала новые' },
  { value: '-rating_avg', label: 'По рейтингу' },
  { value: '-ratings_count', label: 'По числу оценок' },
];

export function CatalogPage({ kind }: { kind: CatalogKind }) {
  const [search_params, set_search_params] = useSearchParams();
  const sorts = [
    ...COMMON_SORTS,
    { value: kind === 'artists' ? 'name' : 'title', label: 'По названию' },
    ...(kind === 'albums' ? [{ value: '-release_date', label: 'По дате выпуска' }] : []),
    ...(kind === 'tracks' ? [{ value: 'duration', label: 'По длительности' }] : []),
  ];
  const requested_sort = search_params.get('sort') || '-created_at';
  const sort = sorts.some((option) => option.value === requested_sort)
    ? requested_sort
    : '-created_at';
  const raw_offset = Number(search_params.get('offset') || 0);
  const offset = Number.isSafeInteger(raw_offset) && raw_offset >= 0 ? raw_offset : 0;
  function change_offset(next_offset: number) {
    set_search_params({ sort, offset: String(next_offset) });
  }
  return (
    <>
      <div className="page-intro">
        <span className="eyebrow">ОТКРЫВАЙТЕ. СЛУШАЙТЕ. ОЦЕНИВАЙТЕ.</span>
        <h1>
          {TITLES[kind]}
          <span className="heading-dot">.</span>
        </h1>
        <p className="muted">{SUBTITLES[kind]}</p>
      </div>
      <div className="catalog-toolbar">
        <nav className="tabs" aria-label="Каталог">
          <Link to="/tracks" aria-current={kind === 'tracks' ? 'page' : undefined}>
            Треки
          </Link>
          <Link to="/albums" aria-current={kind === 'albums' ? 'page' : undefined}>
            Альбомы
          </Link>
          <Link to="/artists" aria-current={kind === 'artists' ? 'page' : undefined}>
            Артисты
          </Link>
        </nav>
        <label className="sort-control">
          Сортировка
          <select
            value={sort}
            onChange={(event) => set_search_params({ sort: event.target.value, offset: '0' })}
          >
            {sorts.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
      </div>
      <CatalogList key={kind} kind={kind} sort={sort} offset={offset} on_change={change_offset} />
    </>
  );
}

export function CatalogSection({
  kind,
  filters,
  title,
}: {
  kind: CatalogKind;
  filters: CatalogFilters;
  title: string;
}) {
  const [offset, set_offset] = useState(0);
  return (
    <section className="catalog-section">
      <h2>{title}</h2>
      <CatalogList kind={kind} filters={filters} offset={offset} on_change={set_offset} />
    </section>
  );
}

function CatalogList({
  kind,
  filters = {},
  sort = '-created_at',
  offset,
  on_change,
}: {
  kind: CatalogKind;
  filters?: CatalogFilters;
  sort?: string;
  offset: number;
  on_change: (offset: number) => void;
}) {
  const { user } = use_auth();
  const query = useQuery({
    queryKey: ['catalog', user?.id, kind, sort, offset, filters],
    queryFn: ({ signal }) => catalog_page(kind, offset, sort, filters, signal),
  });
  if (query.isPending) return <LoadingState />;
  if (query.isError) return <ErrorState error={query.error} retry={() => void query.refetch()} />;
  return (
    <>
      <div className="results-count muted">
        {query.data.total} в каталоге{query.isFetching && ' · обновление…'}
      </div>
      {query.data.items.length ? (
        <div className="catalog-grid">
          {query.data.items.map((item) => (
            <CatalogCard key={item.id} item={item} kind={kind} />
          ))}
        </div>
      ) : (
        <EmptyState
          description={offset ? 'На этой странице ничего нет. Вернитесь на предыдущую.' : undefined}
        />
      )}
      <Pagination
        total={query.data.total}
        offset={offset}
        limit={query.data.limit || PAGE_LIMIT}
        on_change={on_change}
      />
    </>
  );
}

export function CatalogCard({
  item,
  kind,
  is_playable,
}: {
  item: CatalogItem;
  kind: CatalogKind;
  is_playable?: boolean;
}) {
  const player = use_player();
  const name = 'name' in item ? item.name : item.title;
  const url = 'image_url' in item ? item.image_url : 'cover_url' in item ? item.cover_url : null;
  return (
    <article className="catalog-card">
      <Link
        className={`card-art ${kind === 'artists' ? 'artist-art' : ''}`}
        to={`/${kind}/${item.id}`}
      >
        <Cover url={url} name={name} />
        <span className="card-open">
          <ArrowUpRight size={20} />
        </span>
      </Link>
      <div className="card-body">
        <small className="eyebrow">
          {kind === 'tracks' ? 'ТРЕК' : kind === 'albums' ? 'АЛЬБОМ' : 'АРТИСТ'}
          {'duration' in item ? ` · ${format_duration(item.duration)}` : ''}
        </small>
        <h3>
          <Link to={`/${kind}/${item.id}`}>{name}</Link>
        </h3>
        {'artists' in item && (
          <p className="muted card-artists">
            {(item.artists || []).map((artist) => artist.name).join(', ') || 'Артисты не указаны'}
          </p>
        )}
        <RatingBadge
          rating_avg={item.rating_avg}
          ratings_count={item.ratings_count}
          my_rating={item.my_rating}
        />
        {'duration' in item && (
          <div className="card-actions">
            <button
              className="button small"
              disabled={is_playable === false}
              aria-label={`Слушать ${name}`}
              onClick={() => player.play([item])}
            >
              <Play size={14} />
              Слушать
            </button>
            <button
              className="icon-button"
              disabled={is_playable === false}
              aria-label={`Добавить ${name} в очередь`}
              onClick={() => player.append(item)}
            >
              <ListPlus size={18} />
            </button>
          </div>
        )}
      </div>
    </article>
  );
}
