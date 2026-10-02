import { Select } from '../../components/Select';
import { can_create_scene } from '../../app/permissions';
import { Link, useSearchParams } from 'react-router';
import { useQuery } from '@tanstack/react-query';
import { ArrowUpRight, Disc3, Mic2, Upload } from 'lucide-react';
import type { CatalogKind } from '../../api/catalog';
import { format_duration } from '../../app/constants';
import { AuthRequired } from '../../components/AuthRequired';
import { Cover } from '../../components/Cover';
import { Pagination } from '../../components/Pagination';
import { EmptyState, ErrorState, LoadingState } from '../../components/States';
import { use_auth } from '../auth/AuthProvider';
import { studio_page } from './api';

const STUDIO_TABS: { kind: CatalogKind; label: string }[] = [
  { kind: 'artists', label: 'Артисты' },
  { kind: 'albums', label: 'Альбомы' },
  { kind: 'tracks', label: 'Треки' },
];

function Publications() {
  const { user } = use_auth();
  const [search, set_search] = useSearchParams();
  const kind = STUDIO_TABS.find((tab) => tab.kind === search.get('kind'))?.kind || 'artists';
  const raw_offset = Number(search.get('offset'));
  const offset = Number.isSafeInteger(raw_offset) && raw_offset > 0 ? raw_offset : 0;
  const title_sort = kind === 'artists' ? 'name' : 'title';
  const sorts = [
    { value: '-created_at', label: 'Недавно добавленные' },
    { value: title_sort, label: 'По названию' },
    { value: '-rating_avg', label: 'По рейтингу' },
  ];
  const sort = sorts.find((entry) => entry.value === search.get('sort'))?.value || '-created_at';
  const query = useQuery({
    queryKey: ['studio', user?.id, kind, offset, sort],
    queryFn: ({ signal }) => studio_page(kind, offset, sort, signal),
  });
  return (
    <section className="panel studio-publications" aria-labelledby="publications-heading">
      <div className="section-heading">
        <h2 id="publications-heading">Мои публикации</h2>
        <Link className="text-button" to={`/studio/${kind}/new`}>
          {kind === 'artists' ? 'Новый артист' : kind === 'albums' ? 'Новый альбом' : 'Новый трек'}{' '}
          <ArrowUpRight size={16} />
        </Link>
      </div>
      <div className="catalog-toolbar">
        <nav className="tabs" aria-label="Мои публикации">
          {STUDIO_TABS.map((tab) => (
            <Link
              key={tab.kind}
              to={`/studio?kind=${tab.kind}`}
              aria-current={kind === tab.kind ? 'page' : undefined}
            >
              {tab.label}
            </Link>
          ))}
        </nav>
        <label className="sort-control">
          Сортировка публикаций
          <Select
            label="Сортировка публикаций"
            value={sort}
            on_change={(next_value) => set_search({ kind, sort: next_value })}
          >
            {sorts.map((entry) => (
              <option key={entry.value} value={entry.value}>
                {entry.label}
              </option>
            ))}
          </Select>
        </label>
      </div>
      {query.isPending ? (
        <LoadingState />
      ) : query.isError ? (
        <ErrorState error={query.error} retry={() => void query.refetch()} />
      ) : (
        <>
          <p className="muted results-count">Всего: {query.data.total}</p>
          {!query.data.items.length ? (
            <EmptyState
              title={
                offset
                  ? 'На этой странице нет записей'
                  : kind === 'artists'
                    ? 'Создайте своего артиста'
                    : kind === 'albums'
                      ? 'Альбомов пока нет'
                      : 'Треков пока нет'
              }
              description={
                offset
                  ? 'Вернитесь на предыдущую страницу.'
                  : 'Все записи вашего аккаунта будут появляться здесь на любом устройстве.'
              }
            />
          ) : (
            <div className="publication-list">
              {query.data.items.map((item) => {
                const name = 'name' in item ? item.name : item.title;
                return (
                  <article className="publication-row" key={`${kind}:${item.id}`}>
                    <Link
                      className="publication-identity"
                      to={`/${kind}/${item.id}`}
                      aria-label={name}
                    >
                      <Cover
                        name={name}
                        url={
                          'image_url' in item
                            ? item.image_url
                            : 'cover_url' in item
                              ? item.cover_url
                              : null
                        }
                      />
                      <div>
                        <strong>{name}</strong>
                        {'duration' in item && <small>{format_duration(item.duration)}</small>}
                        {'artists' in item && (
                          <small>{item.artists?.map((artist) => artist.name).join(', ')}</small>
                        )}
                      </div>
                    </Link>
                    <div className="actions">
                      <Link
                        className="button small"
                        to={`/studio/${kind}/${item.id}`}
                        aria-label={`Редактировать ${name}`}
                      >
                        Редактировать
                      </Link>
                      {kind === 'artists' && (
                        <Link
                          className="text-button"
                          to={`/studio/tracks/new?artist_id=${item.id}`}
                          aria-label={`Загрузить трек артиста ${name}`}
                        >
                          Загрузить трек →
                        </Link>
                      )}
                      {kind === 'albums' && (
                        <Link
                          className="text-button"
                          to={`/studio/tracks/new?album_id=${item.id}`}
                          aria-label={`Добавить трек в альбом ${name}`}
                        >
                          Добавить трек →
                        </Link>
                      )}
                    </div>
                  </article>
                );
              })}
            </div>
          )}
          <Pagination
            total={query.data.total}
            offset={offset}
            on_change={(value) => set_search({ kind, sort, offset: String(value) })}
          />
        </>
      )}
    </section>
  );
}

export function StudioPage() {
  return (
    <AuthRequired>
      <StudioContent />
    </AuthRequired>
  );
}
function StudioContent() {
  const { user, experience } = use_auth();
  return (
    <>
      <div className="page-intro">
        <span className="eyebrow">СТУДИЯ / LOCALS</span>
        <h1>
          Пусть услышат<span className="heading-dot">.</span>
        </h1>
        <p className="muted">
          Запись из комнаты, первый релиз, музыка своей сцены. Место для вашего звука.
        </p>
      </div>
      <div className="studio-steps">
        <Link className="panel studio-step" to="/studio/artists/new">
          <Mic2 />
          <span className="eyebrow">01 / ИМЯ</span>
          <h2>Создать артиста</h2>
          <p>Представьтесь и расскажите, кто стоит за музыкой.</p>
          <span className="text-button">
            Начать <ArrowUpRight size={16} />
          </span>
        </Link>
        <Link className="panel studio-step" to="/studio/albums/new">
          <Disc3 />
          <span className="eyebrow">02 / РЕЛИЗ</span>
          <h2>Добавить альбом</h2>
          <p>Соберите треки в релиз. Для сингла альбом необязателен.</p>
          <span className="text-button">
            Создать релиз <ArrowUpRight size={16} />
          </span>
        </Link>
        <Link className="panel studio-step" to="/studio/tracks/new">
          <Upload />
          <span className="eyebrow">03 / ЗВУК</span>
          <h2>Загрузить трек</h2>
          <p>Добавьте аудио, обложку и участников записи.</p>
          <span className="text-button">
            Опубликовать <ArrowUpRight size={16} />
          </span>
        </Link>
      </div>
      <Publications />
      {can_create_scene(user?.level, experience) && (
        <div className="actions">
          <Link className="button" to="/events/new">
            Добавить событие
          </Link>
          <Link className="button" to="/venues/new">
            Добавить площадку
          </Link>
        </div>
      )}
    </>
  );
}
