import { Select } from '../../components/Select';
import { ProposalCard, LEVEL_NAMES } from '../auth/ContributionPage';
import { useState, type FormEvent } from 'react';
import { Link, useSearchParams } from 'react-router';
import { useMutation, useQuery } from '@tanstack/react-query';
import type { components } from '../../api/generated';
import { can_moderate } from '../../app/permissions';
import { DESCRIPTION_MAX_LENGTH, NAME_MAX_LENGTH, PAGE_LIMIT } from '../../app/constants';
import { invalidate_music } from '../../app/query';
import { ApiError } from '../../api/errors';
import { AuthRequired } from '../../components/AuthRequired';
import { CityPicker } from '../../components/CityPicker';
import { ErrorState, LoadingState, EmptyState } from '../../components/States';
import { Pagination } from '../../components/Pagination';
import { ImageUpload } from '../studio/ImageUpload';
import { use_auth } from '../auth/AuthProvider';
import { admin_request } from './api';

type User = components['schemas']['AdminUserOut'];
type Proposal = components['schemas']['ContributionOut'];
type Item = {
  id: number;
  name?: string;
  title?: string;
  display_name?: string;
  email?: string;
  level?: string;
  experience_points?: number;
  is_active?: boolean;
  kind?: string;
  visibility?: string;
  action?: string;
  text?: string;
  author?: { display_name: string };
  created_at?: string;
  payload?: unknown;
};
type Page = { items: Item[]; total: number; offset: number; limit: number };
const SECTIONS: Record<string, string> = {
  contributions: 'Проверка правок',
  users: 'Пользователи',
  profiles: 'Публичные профили',
  artists: 'Артисты',
  albums: 'Альбомы',
  tracks: 'Треки',
  venues: 'Площадки',
  events: 'События',
  genres: 'Жанры',
  cities: 'Города',
  playlists: 'Плейлисты',
  reviews: 'Рецензии',
  audit: 'Журнал действий',
};
const RESTRICTED = new Set(['users', 'audit']);

export function AdminPage() {
  return (
    <AuthRequired>
      <Management />
    </AuthRequired>
  );
}

function Management() {
  const { user } = use_auth();
  const [search, set_search] = useSearchParams();
  const section = search.get('section') || 'contributions';
  if (!can_moderate(user?.level))
    return (
      <ErrorState error={new ApiError(403, 'Раздел доступен модераторам и администраторам.')} />
    );
  if (!SECTIONS[section] || (RESTRICTED.has(section) && user?.level !== 'admin'))
    return <ErrorState error={new ApiError(403, 'Этот раздел доступен только администратору.')} />;
  return (
    <>
      <div className="page-intro">
        <span className="eyebrow">УПРАВЛЕНИЕ / LOCALS</span>
        <h1>{user?.level === 'admin' ? 'Администрирование' : 'Модерация'}</h1>
        <p className="muted">Проверяйте предложения участников и управляйте содержимым каталога.</p>
      </div>
      <nav className="admin-tabs" aria-label="Разделы управления">
        {Object.entries(SECTIONS)
          .filter(([key]) => !RESTRICTED.has(key) || user?.level === 'admin')
          .map(([key, label]) => (
            <button
              key={key}
              className={`button ${section === key ? 'primary' : ''}`}
              onClick={() => set_search({ section: key })}
            >
              {label}
            </button>
          ))}
      </nav>
      {section === 'contributions' ? (
        <ModerationQueue />
      ) : (
        <EntityList key={section} section={section} />
      )}
    </>
  );
}

function EntityList({ section }: { section: string }) {
  const { user } = use_auth();
  const [offset, set_offset] = useState(0);
  const [q, set_q] = useState('');
  const [editing, set_editing] = useState<number | 'new' | null>(null);
  const [deleting, set_deleting] = useState<Item | null>(null);
  const private_section =
    RESTRICTED.has(section) ||
    section === 'profiles' ||
    (section === 'playlists' && user?.level === 'admin');
  const endpoint = (private_section ? '/admin/' : '/') + section;
  const query = useQuery({
    queryKey: ['admin', user?.id, section, offset, q],
    queryFn: () =>
      admin_request<Page>(
        endpoint +
          `?limit=${PAGE_LIMIT}&offset=${offset}` +
          (section === 'users' && q ? '&q=' + encodeURIComponent(q) : ''),
      ),
  });
  const deletion = useMutation({
    mutationFn: (item: Item) =>
      admin_request(
        '/' +
          (['cities', 'genres', 'venues'].includes(section) ? 'admin/' : '') +
          section +
          '/' +
          item.id,
        'DELETE',
      ),
    onSuccess: async () => {
      set_deleting(null);
      await invalidate_music();
    },
  });
  const reference = section === 'genres' || section === 'cities';
  const create_path = ['artists', 'albums', 'tracks'].includes(section)
    ? '/studio/' + section + '/new'
    : ['venues', 'events'].includes(section)
      ? '/' + section + '/new'
      : null;
  function editor(item: Item) {
    if (['artists', 'albums', 'tracks'].includes(section))
      return '/studio/' + section + '/' + item.id;
    if (['venues', 'events'].includes(section)) return '/' + section + '/' + item.id + '/edit';
    if (section === 'playlists') return '/playlists/' + item.id;
    return null;
  }
  return (
    <>
      <div className="section-heading">
        <h2>{SECTIONS[section]}</h2>
        {reference ? (
          <button className="button primary" onClick={() => set_editing('new')}>
            Добавить
          </button>
        ) : (
          create_path && (
            <Link className="button primary" to={create_path}>
              Добавить
            </Link>
          )
        )}
      </div>
      {section === 'users' && (
        <label>
          Поиск по имени или email
          <input
            value={q}
            onChange={(event) => {
              set_q(event.target.value);
              set_offset(0);
            }}
          />
        </label>
      )}
      {editing !== null &&
        (section === 'users' ? (
          <UserEditor key={editing} id={Number(editing)} on_close={() => set_editing(null)} />
        ) : reference ? (
          <ReferenceEditor
            key={editing}
            section={section}
            id={editing === 'new' ? undefined : editing}
            on_close={() => set_editing(null)}
          />
        ) : section === 'profiles' ? (
          <ProfileEditor key={editing} id={Number(editing)} on_close={() => set_editing(null)} />
        ) : section === 'reviews' ? (
          <ReviewEditor key={editing} id={Number(editing)} on_close={() => set_editing(null)} />
        ) : null)}
      {query.isPending ? (
        <LoadingState />
      ) : query.isError ? (
        <ErrorState error={query.error} retry={() => void query.refetch()} />
      ) : !query.data.items.length ? (
        <EmptyState title="Записей пока нет" />
      ) : (
        <div className="admin-list">
          {query.data.items.map((item) => (
            <article className="panel" key={item.id}>
              <div className="section-heading">
                <strong>
                  {item.name ||
                    item.title ||
                    item.display_name ||
                    item.action ||
                    `Запись №${item.id}`}
                </strong>
                <span className="muted">№{item.id}</span>
              </div>
              {item.email && (
                <p>
                  {item.email} · {item.level} · {item.experience_points} баллов ·{' '}
                  {item.is_active ? 'Активен' : 'Заблокирован'}
                </p>
              )}
              {item.visibility && (
                <p className="muted">
                  {item.kind === 'liked' ? 'Системный Liked' : 'Подборка'} ·{' '}
                  {item.visibility === 'private' ? 'Приватная' : 'Публичная'}
                </p>
              )}
              {item.text && <p className="preserve-lines">{item.text}</p>}
              {section === 'audit' && (
                <>
                  <small>
                    {item.created_at && new Date(item.created_at).toLocaleString('ru-RU')}
                  </small>
                  <pre className="admin-diff">{JSON.stringify(item.payload, null, 2)}</pre>
                </>
              )}
              {section !== 'audit' && (
                <div className="actions">
                  {editor(item) ? (
                    <Link className="button" to={editor(item)!}>
                      {item.kind === 'liked' ? 'Просмотреть' : 'Редактировать'}
                    </Link>
                  ) : (
                    <button className="button" onClick={() => set_editing(item.id)}>
                      Редактировать
                    </button>
                  )}
                  {!['users', 'profiles'].includes(section) && item.kind !== 'liked' && (
                    <button className="button danger" onClick={() => set_deleting(item)}>
                      Удалить
                    </button>
                  )}
                </div>
              )}
            </article>
          ))}
        </div>
      )}
      {query.data && <Pagination total={query.data.total} offset={offset} on_change={set_offset} />}
      {deleting && (
        <div className="panel confirmation" role="alertdialog" aria-label="Удаление записи">
          <p>Удалить «{deleting.name || deleting.title || deleting.id}»? Действие необратимо.</p>
          <button
            className="button danger"
            disabled={deletion.isPending}
            onClick={() => deletion.mutate(deleting)}
          >
            Удалить
          </button>
          <button className="button" onClick={() => set_deleting(null)}>
            Отмена
          </button>
        </div>
      )}
      {deletion.isError && <ErrorState error={deletion.error} />}
    </>
  );
}

function UserEditor({ id, on_close }: { id: number; on_close: () => void }) {
  const query = useQuery({
    queryKey: ['admin', 'user', id],
    queryFn: () => admin_request<User>('/admin/users/' + id),
  });
  if (query.isPending) return <LoadingState />;
  if (query.isError) return <ErrorState error={query.error} />;
  return <UserForm key={query.data.updated_at} initial={query.data} on_close={on_close} />;
}

function UserForm({ initial, on_close }: { initial: User; on_close: () => void }) {
  const { experience } = use_auth();
  const [name, set_name] = useState(initial.display_name);
  const [email, set_email] = useState(initial.email);
  const [bio, set_bio] = useState(initial.bio || '');
  const [city_id, set_city_id] = useState(initial.city?.id || null);
  const [level, set_level] = useState(initial.level);
  const [tier, set_tier] = useState(
    experience
      ? experience.thresholds.slice(1).filter((value) => (initial.experience_points || 0) >= value)
          .length
      : 0,
  );
  const [scene_verified, set_scene_verified] = useState(initial.scene_verified);
  const [is_active, set_is_active] = useState(initial.is_active);
  const [confirm, set_confirm] = useState(false);
  const mutation = useMutation({
    mutationFn: async () => {
      await admin_request('/admin/users/' + initial.id, 'PATCH', {
        display_name: name,
        email,
        bio: bio || null,
        city_id,
      });
      if (level !== initial.level)
        await admin_request('/admin/users/' + initial.id + '/level', 'PUT', { level });
      const initial_tier = experience
        ? experience.thresholds
            .slice(1)
            .filter((value) => (initial.experience_points || 0) >= value).length
        : 0;
      if (tier !== initial_tier)
        await admin_request('/admin/users/' + initial.id + '/experience', 'PUT', { tier });
      if (scene_verified !== initial.scene_verified || tier !== initial_tier)
        await admin_request('/admin/users/' + initial.id + '/scene-verification', 'PUT', {
          scene_verified,
        });
      if (is_active !== initial.is_active)
        await admin_request('/admin/users/' + initial.id + '/status', 'PUT', { is_active });
    },
    onSuccess: async () => {
      await invalidate_music();
      on_close();
    },
  });
  function submit(event: FormEvent) {
    event.preventDefault();
    set_confirm(true);
  }
  return (
    <>
      <form className="panel form" onSubmit={submit}>
        <h3>Аккаунт: {initial.display_name}</h3>
        <label>
          Имя
          <input
            required
            value={name}
            maxLength={NAME_MAX_LENGTH}
            onChange={(event) => set_name(event.target.value)}
          />
        </label>
        <label>
          Email
          <input
            type="email"
            required
            value={email}
            onChange={(event) => set_email(event.target.value)}
          />
        </label>
        <label>
          Описание
          <textarea
            value={bio}
            maxLength={DESCRIPTION_MAX_LENGTH}
            onChange={(event) => set_bio(event.target.value)}
          />
        </label>
        <CityPicker value={city_id} on_change={set_city_id} />
        {initial.level === 'admin' ? (
          <p className="muted">
            Права и активность администратора меняются только из терминала разработчика.
          </p>
        ) : (
          <>
            <label>
              Роль
              <Select
                label="Роль"
                value={level}
                on_change={(next_value) => {
                  const value = next_value as User['level'];
                  set_level(value);
                  if (value === 'green') {
                    set_tier(0);
                    set_scene_verified(false);
                  }
                  if (value === 'experienced' && tier === 0) set_tier(1);
                }}
              >
                <option value="green">Пользователь</option>
                <option value="experienced">Опытный участник</option>
                <option value="moderator">Модератор</option>
              </Select>
            </label>
            <label>
              Уровень опыта
              <Select
                label="Уровень опыта"
                value={tier}
                on_change={(next_value) => {
                  const value = Number(next_value);
                  set_tier(value);
                  set_scene_verified(value >= 3);
                  if (level !== 'moderator') set_level(value ? 'experienced' : 'green');
                }}
                disabled={!experience}
              >
                {LEVEL_NAMES.map((name, index) => (
                  <option key={index} value={index}>
                    {index + 1} - {name}
                  </option>
                ))}
              </Select>
            </label>
            <label>
              <input
                type="checkbox"
                checked={scene_verified}
                onChange={(event) => set_scene_verified(event.target.checked)}
              />{' '}
              Подтверждённый организатор: публикация без очереди
            </label>
            <p className="muted">
              Уровень можно назначить вручную. При назначении уровня от 4 владелец получает
              подтверждённый статус организатора и публикует площадки и события без очереди. Опыт не
              назначает модератора. При изменении роли, ступени или блокировке пользователь должен
              войти снова.
            </p>
            <label>
              <input
                type="checkbox"
                checked={is_active}
                onChange={(event) => set_is_active(event.target.checked)}
              />{' '}
              Аккаунт активен
            </label>
          </>
        )}
        {!confirm ? (
          <button className="button primary" disabled={mutation.isPending}>
            Сохранить
          </button>
        ) : (
          <div className="confirmation" role="alertdialog" aria-label="Изменение пользователя">
            <p>Применить изменения к аккаунту {initial.email}?</p>
            <button
              type="button"
              className="button primary"
              disabled={mutation.isPending}
              onClick={() => mutation.mutate()}
            >
              Подтвердить
            </button>
            <button type="button" className="button" onClick={() => set_confirm(false)}>
              Вернуться
            </button>
          </div>
        )}
        <button type="button" className="text-button" onClick={on_close}>
          Закрыть редактор
        </button>
        {mutation.isError && <ErrorState error={mutation.error} />}
      </form>
      <ImageUpload target_type="user" target_id={initial.id} />
      <CommunityAwardEditor id={initial.id} />
    </>
  );
}

function ReferenceEditor({
  section,
  id,
  on_close,
}: {
  section: string;
  id?: number;
  on_close: () => void;
}) {
  const query = useQuery({
    queryKey: ['admin', section, 'reference', id],
    enabled: !!id,
    queryFn: async () => {
      let offset = 0;
      while (true) {
        const page = await admin_request<{ items: Record<string, unknown>[]; total: number }>(
          '/' + section + `?limit=100&offset=${offset}`,
        );
        const item = page.items.find((value) => value.id === id);
        if (item) return item;
        offset += page.items.length;
        if (!page.items.length || offset >= page.total)
          throw new ApiError(404, 'Запись не найдена.');
      }
    },
  });
  if (id && query.isPending) return <LoadingState />;
  if (query.isError) return <ErrorState error={query.error} />;
  return (
    <ReferenceForm
      key={id || 'new'}
      section={section}
      id={id}
      initial={query.data}
      on_close={on_close}
    />
  );
}

function ReferenceForm({
  section,
  id,
  initial,
  on_close,
}: {
  section: string;
  id?: number;
  initial?: Record<string, unknown>;
  on_close: () => void;
}) {
  const fields =
    section === 'genres'
      ? ['name', 'slug']
      : ['name', 'region', 'country', 'lat', 'lng', 'timezone'];
  const [values, set_values] = useState<Record<string, string>>(
    Object.fromEntries(
      fields.map((field) => [
        field,
        String(initial?.[field] ?? (field === 'timezone' ? 'Asia/Yekaterinburg' : '')),
      ]),
    ),
  );
  const mutation = useMutation({
    mutationFn: () =>
      admin_request(
        (id ? '/admin/' : '/') + section + (id ? '/' + id : ''),
        id ? 'PUT' : 'POST',
        section === 'genres'
          ? values
          : {
              ...values,
              region: values.region || null,
              lat: Number(values.lat),
              lng: Number(values.lng),
            },
      ),
    onSuccess: async () => {
      await invalidate_music();
      on_close();
    },
  });
  const labels: Record<string, string> = {
    name: 'Название',
    slug: 'Slug латиницей',
    region: 'Регион',
    country: 'Страна',
    lat: 'Широта',
    lng: 'Долгота',
    timezone: 'Часовой пояс',
  };
  return (
    <form
      className="panel form"
      onSubmit={(event) => {
        event.preventDefault();
        mutation.mutate();
      }}
    >
      <h3>{id ? 'Редактирование' : 'Новая запись'}</h3>
      {fields.map((field) => (
        <label key={field}>
          {labels[field]}
          <input
            required={field !== 'region'}
            type={['lat', 'lng'].includes(field) ? 'number' : 'text'}
            step={['lat', 'lng'].includes(field) ? 'any' : undefined}
            value={values[field]}
            onChange={(event) => set_values({ ...values, [field]: event.target.value })}
          />
        </label>
      ))}
      <button className="button primary" disabled={mutation.isPending}>
        Сохранить
      </button>
      <button type="button" className="text-button" onClick={on_close}>
        Отмена
      </button>
      {mutation.isError && <ErrorState error={mutation.error} />}
    </form>
  );
}

function ReviewEditor({ id, on_close }: { id: number; on_close: () => void }) {
  const query = useQuery({
    queryKey: ['admin', 'review', id],
    queryFn: () => admin_request<components['schemas']['ReviewOut']>('/reviews/' + id),
  });
  if (query.isPending) return <LoadingState />;
  if (query.isError) return <ErrorState error={query.error} />;
  return <ReviewForm initial={query.data} on_close={on_close} />;
}
function ReviewForm({
  initial,
  on_close,
}: {
  initial: components['schemas']['ReviewOut'];
  on_close: () => void;
}) {
  const [title, set_title] = useState(initial.title || '');
  const [text, set_text] = useState(initial.text);
  const mutation = useMutation({
    mutationFn: () =>
      admin_request('/reviews/' + initial.id, 'PATCH', { title: title || null, text }),
    onSuccess: async () => {
      await invalidate_music();
      on_close();
    },
  });
  return (
    <form
      className="panel form"
      onSubmit={(event) => {
        event.preventDefault();
        mutation.mutate();
      }}
    >
      <h3>Рецензия: {initial.author.display_name}</h3>
      <label>
        Заголовок
        <input value={title} onChange={(event) => set_title(event.target.value)} />
      </label>
      <label>
        Текст
        <textarea required value={text} onChange={(event) => set_text(event.target.value)} />
      </label>
      <p className="muted">Личная оценка автора сохраняется.</p>
      <button className="button primary" disabled={mutation.isPending}>
        Сохранить
      </button>
      <button type="button" className="text-button" onClick={on_close}>
        Отмена
      </button>
      {mutation.isError && <ErrorState error={mutation.error} />}
    </form>
  );
}

function ModerationQueue() {
  const { user } = use_auth();
  const [offset, set_offset] = useState(0);
  const [status, set_status] = useState('pending');
  const query = useQuery({
    queryKey: ['contributions', 'moderation', user?.id, status, offset],
    queryFn: () =>
      admin_request<{ items: Proposal[]; total: number }>(
        '/admin/contributions?status=' + status + `&limit=${PAGE_LIMIT}&offset=${offset}`,
      ),
  });
  return (
    <>
      <div className="section-heading">
        <h2>Предложения участников</h2>
        <Select
          label="Статус заявки"
          value={status}
          on_change={(next_value) => {
            set_status(next_value);
            set_offset(0);
          }}
        >
          <option value="pending">Ожидают проверки</option>
          <option value="approved">Приняты</option>
          <option value="rejected">Отклонены</option>
        </Select>
      </div>
      {query.isPending ? (
        <LoadingState />
      ) : query.isError ? (
        <ErrorState error={query.error} />
      ) : !query.data.items.length ? (
        <EmptyState title="Заявок пока нет" />
      ) : (
        query.data.items.map((proposal) => <ProposalCard key={proposal.id} proposal={proposal} />)
      )}
      {query.data && <Pagination total={query.data.total} offset={offset} on_change={set_offset} />}
    </>
  );
}

function ProfileEditor({ id, on_close }: { id: number; on_close: () => void }) {
  const query = useQuery({
    queryKey: ['profile', id],
    queryFn: () => admin_request<components['schemas']['UserOut']>('/users/' + id),
  });
  if (query.isPending) return <LoadingState />;
  if (query.isError) return <ErrorState error={query.error} />;
  return <ProfileForm initial={query.data} on_close={on_close} />;
}
function ProfileForm({
  initial,
  on_close,
}: {
  initial: components['schemas']['UserOut'];
  on_close: () => void;
}) {
  const [name, set_name] = useState(initial.display_name);
  const [bio, set_bio] = useState(initial.bio || '');
  const [city_id, set_city_id] = useState(initial.city?.id || null);
  const mutation = useMutation({
    mutationFn: () =>
      admin_request('/admin/profiles/' + initial.id, 'PATCH', {
        display_name: name,
        bio: bio || null,
        city_id,
      }),
    onSuccess: async () => {
      await invalidate_music();
      on_close();
    },
  });
  return (
    <>
      <form
        className="panel form"
        onSubmit={(event) => {
          event.preventDefault();
          mutation.mutate();
        }}
      >
        <h3>Публичный профиль: {initial.display_name}</h3>
        <label>
          Имя
          <input
            required
            maxLength={NAME_MAX_LENGTH}
            value={name}
            onChange={(event) => set_name(event.target.value)}
          />
        </label>
        <label>
          Описание
          <textarea
            maxLength={DESCRIPTION_MAX_LENGTH}
            value={bio}
            onChange={(event) => set_bio(event.target.value)}
          />
        </label>
        <CityPicker value={city_id} on_change={set_city_id} />
        <button className="button primary" disabled={mutation.isPending}>
          Сохранить профиль
        </button>
        <button type="button" className="button" onClick={on_close}>
          Закрыть
        </button>
        {mutation.isError && <ErrorState error={mutation.error} />}
      </form>
      <ImageUpload target_type="user" target_id={initial.id} />
    </>
  );
}
function CommunityAwardEditor({ id }: { id: number }) {
  const [kind, set_kind] = useState<'curator_week' | 'reviewer_month'>('curator_week');
  const [period, set_period] = useState('');
  const [confirmation, set_confirmation] = useState(false);
  const mutation = useMutation({
    mutationFn: () =>
      admin_request(`/admin/users/${id}/community-awards`, 'POST', { kind, period }),
    onSuccess: async () => {
      set_confirmation(false);
      await invalidate_music();
    },
  });
  return (
    <form
      className="panel form"
      onSubmit={(event) => {
        event.preventDefault();
        set_confirmation(true);
      }}
    >
      <h3>Награда сообщества</h3>
      <label>
        Номинация
        <Select
          label="Номинация"
          value={kind}
          on_change={(next_value) => set_kind(next_value as typeof kind)}
        >
          <option value="curator_week">Куратор недели</option>
          <option value="reviewer_month">Топ рецензентов месяца</option>
        </Select>
      </label>
      <label>
        Начало периода
        <input
          type="date"
          required
          value={period}
          onChange={(event) => set_period(event.target.value)}
        />
      </label>
      <p className="muted">
        Для недели выберите понедельник, для месяца - первое число. За один период награда выдаётся
        один раз.
      </p>
      {confirmation ? (
        <div className="confirmation" role="alertdialog" aria-label="Награда участнику">
          <p>Выбрать участника победителем за этот период?</p>
          <button
            type="button"
            className="button primary"
            disabled={mutation.isPending}
            onClick={() => mutation.mutate()}
          >
            Выдать награду
          </button>
          <button type="button" className="button" onClick={() => set_confirmation(false)}>
            Отмена
          </button>
        </div>
      ) : (
        <button className="button">Выбрать победителем</button>
      )}
      {mutation.isSuccess && <p role="status">Награда учтена</p>}
      {mutation.isError && <ErrorState error={mutation.error} />}
    </form>
  );
}
