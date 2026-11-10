import { useEffect, useId, useState, type FormEvent } from 'react';
import { Link, useLocation } from 'react-router';
import { useMutation } from '@tanstack/react-query';
import { Star } from 'lucide-react';
import { api, unwrap } from '../../api/client';
import type { RatingTarget } from '../../api/catalog';
import { RATING_VALUES } from '../../app/constants';
import { invalidate_music } from '../../app/query';
import { ErrorState } from '../../components/States';
import { use_auth } from '../auth/AuthProvider';

const RATING_STARS = RATING_VALUES.filter(Number.isInteger);
const STAR_FILL_PERCENT = 100;

export function RatingBadge({
  rating_avg,
  ratings_count,
  my_rating,
}: {
  rating_avg: number | null;
  ratings_count?: number;
  my_rating?: number | null;
}) {
  return (
    <div className="rating-summary">
      <span className="rating-badge" title="Средняя оценка с учётом весов пользователей">
        <Star size={14} aria-hidden="true" />
        {rating_avg == null ? 'Нет оценок' : rating_avg.toFixed(2)}
      </span>
      {ratings_count !== undefined && <small className="muted">{ratings_count} оценок</small>}
      {my_rating != null && <small className="my-rating">Ваша: {my_rating}</small>}
    </div>
  );
}

export function RatingControl({
  target_type,
  target_id,
  my_rating,
}: {
  target_type: RatingTarget;
  target_id: number;
  my_rating: number | null;
}) {
  const { user } = use_auth();
  const location = useLocation();
  const [selected_value, set_selected_value] = useState(my_rating);
  const [preview_value, set_preview_value] = useState<number | null>(null);
  const rating_id = useId();
  const [confirm_delete, set_confirm_delete] = useState(false);
  useEffect(() => set_selected_value(my_rating), [my_rating]);
  const mutation = useMutation({
    mutationFn: async (value: number | null) =>
      value === null
        ? unwrap(
            await api.DELETE('/api/v1/ratings/{target_type}/{target_id}', {
              params: { path: { target_type, target_id } },
            }),
          )
        : unwrap(await api.PUT('/api/v1/ratings', { body: { target_type, target_id, value } })),
    onSuccess: async (_, value) => {
      set_confirm_delete(false);
      set_selected_value(value);
      await invalidate_music();
    },
  });
  if (!user)
    return (
      <div className="panel rate-panel">
        <h2>Как вам эта музыка?</h2>
        <p className="muted">Ваши оценки помогают найти следующий любимый трек.</p>
        <Link
          className="button primary"
          to={`/login?next=${encodeURIComponent(location.pathname)}`}
        >
          Войти и оценить
        </Link>
      </div>
    );
  function submit(event: FormEvent) {
    event.preventDefault();
    if (selected_value !== null) mutation.mutate(selected_value);
  }
  return (
    <div className="panel rate-panel">
      <h2>{my_rating == null ? 'Как вам эта музыка?' : `Ваша оценка: ${my_rating}`}</h2>
      <p className="muted">От 1 до 5 с шагом 0,5. Оценки формируют ваши рекомендации.</p>
      <form className="actions" onSubmit={submit}>
        <fieldset className="rating-field" disabled={mutation.isPending}>
          <legend>Ваша оценка</legend>
          <div className="rating-stars" onPointerLeave={() => set_preview_value(null)}>
            {RATING_STARS.map((star) => (
              <span className="rating-star" key={star}>
                <Star className="star-outline" aria-hidden="true" />
                <span
                  className="star-fill"
                  style={{
                    width: `${Math.max(0, Math.min(1, (preview_value ?? selected_value ?? 0) - star + 1)) * STAR_FILL_PERCENT}%`,
                  }}
                >
                  <Star aria-hidden="true" />
                </span>
                {RATING_VALUES.filter((value) => Math.ceil(value) === star).map((value) => (
                  <label
                    key={value}
                    className={`rating-hit ${star === 1 ? 'star-whole' : Number.isInteger(value) ? 'star-right' : 'star-left'}`}
                    onPointerEnter={() => set_preview_value(value)}
                    onPointerUp={() => set_preview_value(null)}
                  >
                    <input
                      type="radio"
                      name={rating_id}
                      value={value}
                      aria-label={`${value} из 5`}
                      checked={selected_value === value}
                      onChange={() => set_selected_value(value)}
                    />
                  </label>
                ))}
              </span>
            ))}
          </div>
          <small className="muted">
            {selected_value === null ? 'Выберите звезду или её половину' : `${selected_value} из 5`}
          </small>
        </fieldset>
        <button className="button primary" disabled={mutation.isPending || selected_value === null}>
          {my_rating == null ? 'Оценить' : 'Изменить оценку'}
        </button>
        {my_rating != null && (
          <button
            type="button"
            className="text-button"
            disabled={mutation.isPending}
            onClick={() => set_confirm_delete(true)}
          >
            Удалить оценку
          </button>
        )}
      </form>
      {confirm_delete && (
        <div className="confirmation" role="alertdialog" aria-label="Удаление оценки">
          <p>Удаление оценки также удалит вашу рецензию и её лайки.</p>
          <div className="actions">
            <button
              className="button danger"
              disabled={mutation.isPending}
              onClick={() => mutation.mutate(null)}
            >
              Удалить оценку и рецензию
            </button>
            <button
              className="button"
              disabled={mutation.isPending}
              onClick={() => set_confirm_delete(false)}
            >
              Отмена
            </button>
          </div>
        </div>
      )}
      {mutation.isError && <ErrorState error={mutation.error} />}
      {mutation.isSuccess && (
        <p className="success-message" role="status">
          {mutation.variables === null ? 'Оценка удалена.' : 'Оценка сохранена.'} Рекомендации
          обновлены.
        </p>
      )}
    </div>
  );
}
