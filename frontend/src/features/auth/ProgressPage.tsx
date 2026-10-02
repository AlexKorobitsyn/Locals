import { LEVEL_NAMES, ProposalCard } from './ContributionPage';
import { useEffect, useState, type FormEvent } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Link } from 'react-router';
import { api, unwrap } from '../../api/client';
import { invalidate_music } from '../../app/query';
import { PAGE_LIMIT, LYRICS_MAX_LENGTH } from '../../app/constants';
import { can_moderate } from '../../app/permissions';
import { AuthRequired } from '../../components/AuthRequired';
import { GenrePicker } from '../../components/GenrePicker';
import { ErrorState, LoadingState, EmptyState } from '../../components/States';
import { Pagination } from '../../components/Pagination';
import { use_auth } from './AuthProvider';

export function ProgressPage() {
  return (
    <AuthRequired>
      <Progress />
    </AuthRequired>
  );
}
function Progress() {
  const { user, experience } = use_auth();
  const [offset, set_offset] = useState(0);
  const claim = useMutation({
    mutationFn: async () => unwrap(await api.POST('/api/v1/me/experience/claim')),
    onSuccess: invalidate_music,
  });
  useEffect(() => {
    claim.mutate();
  }, [user?.id]);
  const awards = useQuery({
    queryKey: ['experience', 'awards', user?.id],
    queryFn: async () => unwrap(await api.GET('/api/v1/me/experience/awards')),
  });
  const proposals = useQuery({
    queryKey: ['contributions', 'own', user?.id, offset],
    queryFn: async () =>
      unwrap(
        await api.GET('/api/v1/me/contributions', {
          params: { query: { limit: PAGE_LIMIT, offset } },
        }),
      ),
  });
  return (
    <>
      <div className="page-intro">
        <span className="eyebrow">УЧАСТИЕ / LOCALS</span>
        <h1>Мой опыт</h1>
        <p className="muted">
          Слушайте, делитесь открытиями, пишите рецензии и помогайте местной сцене.
        </p>
      </div>
      {!experience ? (
        <LoadingState />
      ) : (
        <>
          <div className="panel">
            <h2>
              {experience.experience_points} XP · уровень {experience.experience_level}:{' '}
              {experience.level_name}
            </h2>
            {experience.next_threshold !== null && (
              <>
                <p>
                  До следующего уровня:{' '}
                  {Math.max(0, experience.next_threshold - experience.experience_points)} XP.
                </p>
                <progress
                  aria-label="Прогресс уровня"
                  max={
                    experience.next_threshold -
                    (experience.thresholds[experience.experience_tier] || 0)
                  }
                  value={
                    experience.experience_points -
                    (experience.thresholds[experience.experience_tier] || 0)
                  }
                />
              </>
            )}
            <p>
              Ваш лимит: {experience.contribution_limit} открытых предложений,{' '}
              {experience.event_limit} будущих событий.
            </p>
            <p>
              Предлагать тексты, жанры, названия, площадки и события можно на любом уровне. Голоса
              сообщества и одобрение владельца превращают полезные предложения в опубликованный
              вклад.
            </p>
            {user?.scene_verified && (
              <p className="eyebrow">
                Подтверждённый организатор — публикация площадок и событий без очереди
              </p>
            )}
            <ul>
              <li>
                Прослушивание почти целиком (95%) — 1 XP, один раз за трек в сутки, до{' '}
                {experience.listen_daily_cap} XP в сутки. Свои треки не учитываются.
              </li>
              <li>
                Первая оценка, добавление чужого трека в свой плейлист, подписка на артиста — 1 XP.
                Всего до {experience.micro_daily_cap} таких наград в сутки. Повторы не дают XP.
              </li>
              <li>
                Рецензия длиннее 200 знаков — {experience.review_points} XP, до{' '}
                {experience.review_daily_cap} в сутки. Один текст и одна цель награждаются только
                один раз.
              </li>
              <li>
                Принятые предложения: текст — 20 XP, жанры и название — 15 XP, площадка — 40 XP,
                событие — 30 XP.
              </li>
              <li>
                За публикацию трека с аудио после первого полного прослушивания другим пользователем
                — 10 XP, максимум одна такая награда в сутки.
              </li>
              <li>
                Ваш трек с аудио, который минимум {experience.quality_min_raters} других слушателей
                оценили в среднем от {experience.quality_min_rating}, —{' '}
                {experience.quality_track_points} XP. Первая такая публикация артиста — ещё 40 XP.
              </li>
              <li>
                10 лайков вашей рецензии, 20 участников вашего события или 100 разных слушателей
                вашего трека — {experience.milestone_points} XP за каждое достижение.
              </li>
              <li>
                Семь дней полезной активности подряд — двойной XP за прослушивания в этот день. За
                простой вход XP нет.
              </li>
              <li>
                Пять состоявшихся событий с участниками на вашей площадке за месяц — 30 XP.
                Кураторов недели и лучших рецензентов месяца выбирает администратор.
              </li>
            </ul>
            <div className="actions">
              <Link className="button" to="/contributions">
                Помочь сообществу
              </Link>
              <Link className="button" to="/venues/new">
                Предложить площадку
              </Link>
              <Link className="button" to="/events/new">
                Предложить событие
              </Link>
            </div>
            <details>
              <summary>Все девять уровней</summary>
              <ol>
                {experience.thresholds.map((threshold, index) => (
                  <li key={threshold}>
                    {LEVEL_NAMES[index]} — от {threshold} XP
                  </li>
                ))}
              </ol>
            </details>
            <button className="button" disabled={claim.isPending} onClick={() => claim.mutate()}>
              Проверить достижения
            </button>
          </div>
        </>
      )}
      {claim.isError && <ErrorState error={claim.error} />}
      <h2>Последние награды</h2>
      {awards.isPending ? (
        <LoadingState />
      ) : awards.isError ? (
        <ErrorState error={awards.error} />
      ) : !awards.data.items.length ? (
        <EmptyState title="Первая награда ещё впереди" />
      ) : (
        <ul>
          {awards.data.items.map((item) => (
            <li key={item.id}>
              +{item.points} XP ·{' '}
              {(
                {
                  listen: 'Прослушивание',
                  micro: 'Участие',
                  review: 'Рецензия',
                  contribution: 'Принятое предложение',
                  quality: 'Хорошая музыка',
                  publication: 'Публикация музыки',
                  artist_discovery: 'Открытие артиста',
                  track_audience: '100 слушателей',
                  review_likes: 'Полезная рецензия',
                  event_audience: 'Участники события',
                  streak: 'Серия активности',
                  venue_month: 'Живая площадка',
                  curator_week: 'Куратор недели',
                  reviewer_month: 'Рецензент месяца',
                } as Record<string, string>
              )[item.kind] || item.kind}{' '}
              · {item.day}
            </li>
          ))}
        </ul>
      )}
      <h2>Мои предложения</h2>
      {proposals.isPending ? (
        <LoadingState />
      ) : proposals.isError ? (
        <ErrorState error={proposals.error} />
      ) : !proposals.data.items.length ? (
        <EmptyState title="Вы пока не предлагали правок" />
      ) : (
        proposals.data.items.map((proposal) => (
          <ProposalCard key={proposal.id} proposal={proposal} />
        ))
      )}
      {proposals.data && (
        <Pagination total={proposals.data.total} offset={offset} on_change={set_offset} />
      )}
    </>
  );
}

export function ContributionForm({
  target_type,
  target_id,
  is_owner,
  current_lyrics,
  genre_ids = [],
}: {
  target_type: 'track' | 'album' | 'artist';
  target_id: number;
  is_owner?: boolean;
  current_lyrics?: string | null;
  genre_ids?: number[];
}) {
  const { user } = use_auth();
  const [open, set_open] = useState(false);
  const [field, set_field] = useState<'lyrics' | 'genres' | 'metadata'>(
    target_type === 'track' ? 'lyrics' : 'genres',
  );
  const [lyrics, set_lyrics] = useState(current_lyrics || '');
  const [genres, set_genres] = useState(genre_ids);
  const [name, set_name] = useState('');
  const mutation = useMutation({
    mutationFn: async () =>
      unwrap(
        await api.POST('/api/v1/contributions', {
          body: {
            target_type,
            target_id,
            field,
            ...(field === 'lyrics'
              ? { lyrics: lyrics || null }
              : field === 'genres'
                ? { genre_ids: genres }
                : { name }),
          },
        }),
      ),
    onSuccess: async () => {
      await invalidate_music();
      set_open(false);
    },
  });
  if (!user) return null;
  if (is_owner || can_moderate(user.level))
    return (
      <section className="panel">
        <Link
          className="button"
          to={`/contributions?target_type=${target_type}&target_id=${target_id}`}
        >
          Предложения к этой записи
        </Link>
      </section>
    );
  function submit(event: FormEvent) {
    event.preventDefault();
    mutation.mutate();
  }
  return (
    <section className="panel">
      {!open ? (
        <>
          <Link
            className="text-button"
            to={`/contributions?target_type=${target_type}&target_id=${target_id}`}
          >
            Голосовать за предложения к этой записи
          </Link>
          <button className="button" onClick={() => set_open(true)}>
            Предложить исправление
          </button>
          {mutation.isSuccess && (
            <p role="status">
              Предложение опубликовано в очереди. До принятия запись не изменится.
            </p>
          )}
        </>
      ) : (
        <form className="form" onSubmit={submit}>
          <h3>Предложение на проверку</h3>
          <label>
            Что изменить
            <select
              value={field}
              onChange={(event) =>
                set_field(event.target.value as 'lyrics' | 'genres' | 'metadata')
              }
            >
              {target_type === 'track' && <option value="lyrics">Текст песни</option>}
              <option value="genres">Жанры</option>
              <option value="metadata">Название</option>
            </select>
          </label>
          {field === 'lyrics' ? (
            <label>
              Предлагаемый текст
              <textarea
                maxLength={LYRICS_MAX_LENGTH}
                value={lyrics}
                onChange={(event) => set_lyrics(event.target.value)}
              />
            </label>
          ) : field === 'genres' ? (
            <GenrePicker value={genres} on_change={set_genres} />
          ) : (
            <label>
              Предлагаемое название
              <input
                required
                value={name}
                maxLength={255}
                onChange={(event) => set_name(event.target.value)}
              />
            </label>
          )}
          <p className="muted">
            Для публикации нужны голоса сообщества или одобрение владельца. За принятую правку
            начисляется XP.
          </p>
          <button className="button primary" disabled={mutation.isPending}>
            Отправить на проверку
          </button>
          <button type="button" className="text-button" onClick={() => set_open(false)}>
            Отмена
          </button>
          {mutation.isError && <ErrorState error={mutation.error} />}
        </form>
      )}
    </section>
  );
}
