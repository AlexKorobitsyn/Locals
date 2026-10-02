import { can_edit_public } from '../../app/permissions';
import { useState, type FormEvent } from 'react';
import { Link } from 'react-router';
import { useMutation, useQuery } from '@tanstack/react-query';
import { api, unwrap } from '../../api/client';
import type { RatingTarget } from '../../api/catalog';
import type { components } from '../../api/generated';
import { NAME_MAX_LENGTH, PAGE_LIMIT, REVIEW_MAX_LENGTH } from '../../app/constants';
import { invalidate_music } from '../../app/query';
import { EmptyState, ErrorState, LoadingState } from '../../components/States';
import { Pagination } from '../../components/Pagination';
import { use_auth } from '../auth/AuthProvider';

type Review = components['schemas']['ReviewOut'];

export function Reviews({
  target_type,
  target_id,
  my_rating,
}: {
  target_type: RatingTarget;
  target_id: number;
  my_rating: number | null;
}) {
  const { user } = use_auth();
  const [offset, set_offset] = useState(0);
  const [editing_review, set_editing_review] = useState<Review | null>(null);
  const [deleting_id, set_deleting_id] = useState<number | null>(null);
  const reviews_query = useQuery({
    queryKey: ['reviews', user?.id, target_type, target_id, offset],
    queryFn: async ({ signal }) =>
      unwrap(
        await api.GET('/api/v1/reviews', {
          params: { query: { target_type, target_id, limit: PAGE_LIMIT, offset } },
          signal,
        }),
      ),
  });
  const deletion = useMutation({
    mutationFn: async (review_id: number) =>
      unwrap(await api.DELETE('/api/v1/reviews/{review_id}', { params: { path: { review_id } } })),
    onSuccess: async () => {
      set_deleting_id(null);
      set_editing_review(null);
      await invalidate_music();
    },
  });
  const own_review = reviews_query.data?.items.find((review) => review.is_owner);
  return (
    <section className="reviews-section">
      <div className="section-heading">
        <h2>Рецензии слушателей</h2>
        <span className="muted">{reviews_query.data?.total || 0}</span>
      </div>
      {user && (editing_review || (my_rating != null && !own_review)) && (
        <ReviewForm
          key={editing_review?.id || 'new'}
          target_type={target_type}
          target_id={target_id}
          review={editing_review}
          on_done={() => set_editing_review(null)}
        />
      )}
      {user && my_rating == null && (
        <p className="muted">Поставьте оценку, чтобы написать рецензию.</p>
      )}
      {reviews_query.isPending ? (
        <LoadingState />
      ) : reviews_query.isError ? (
        <ErrorState error={reviews_query.error} retry={() => void reviews_query.refetch()} />
      ) : !reviews_query.data.items.length ? (
        <EmptyState title="Первое слово за вами" description="У этой музыки ещё нет рецензий." />
      ) : (
        <div className="review-list">
          {reviews_query.data.items.map((review) => (
            <article className="panel review" key={review.id}>
              <div className="section-heading">
                <Link to={`/users/${review.author.id}`}>
                  <strong>{review.author.display_name}</strong>
                </Link>
                <span className="rating-badge">★ {review.rating}</span>
              </div>
              {review.title && <h3>{review.title}</h3>}
              <p className="preserve-lines">{review.text}</p>
              <small className="muted">
                {new Date(review.created_at).toLocaleDateString('ru-RU')}
              </small>
              {can_edit_public(review.is_owner, user?.level) && (
                <div className="actions">
                  <button className="text-button" onClick={() => set_editing_review(review)}>
                    Редактировать
                  </button>
                  <button className="text-button" onClick={() => set_deleting_id(review.id)}>
                    Удалить рецензию
                  </button>
                </div>
              )}
              {deleting_id === review.id && (
                <div className="confirmation" role="alertdialog" aria-label="Удаление рецензии">
                  <p>Удалить рецензию? Оценка останется.</p>
                  <button
                    className="button danger"
                    disabled={deletion.isPending}
                    onClick={() => deletion.mutate(review.id)}
                  >
                    Удалить
                  </button>
                  <button className="button" onClick={() => set_deleting_id(null)}>
                    Отмена
                  </button>
                </div>
              )}
            </article>
          ))}
        </div>
      )}
      {deletion.isError && <ErrorState error={deletion.error} />}
      {reviews_query.data && (
        <Pagination total={reviews_query.data.total} offset={offset} on_change={set_offset} />
      )}
    </section>
  );
}

function ReviewForm({
  target_type,
  target_id,
  review,
  on_done,
}: {
  target_type: RatingTarget;
  target_id: number;
  review: Review | null;
  on_done: () => void;
}) {
  const [title, set_title] = useState(review?.title || '');
  const [text, set_text] = useState(review?.text || '');
  const mutation = useMutation({
    mutationFn: async () =>
      review
        ? unwrap(
            await api.PATCH('/api/v1/reviews/{review_id}', {
              params: { path: { review_id: review.id } },
              body: { title: title.trim() || null, text: text.trim() },
            }),
          )
        : unwrap(
            await api.POST('/api/v1/reviews', {
              body: { target_type, target_id, title: title.trim() || null, text: text.trim() },
            }),
          ),
    onSuccess: async () => {
      set_text('');
      set_title('');
      on_done();
      await invalidate_music();
    },
  });
  function submit(event: FormEvent) {
    event.preventDefault();
    mutation.mutate();
  }
  return (
    <form className="panel form" onSubmit={submit}>
      <h3>{review ? 'Редактировать рецензию' : 'Расскажите, что услышали'}</h3>
      <label>
        Заголовок · необязательно
        <input
          value={title}
          onChange={(event) => set_title(event.target.value)}
          maxLength={NAME_MAX_LENGTH}
        />
      </label>
      <label>
        Ваша рецензия
        <textarea
          value={text}
          onChange={(event) => set_text(event.target.value)}
          maxLength={REVIEW_MAX_LENGTH}
          required
          rows={5}
        />
      </label>
      <div className="actions">
        <button className="button primary" disabled={mutation.isPending || !text.trim()}>
          {review ? 'Сохранить рецензию' : 'Опубликовать рецензию'}
        </button>
        {review && (
          <button className="button" type="button" onClick={on_done}>
            Отмена
          </button>
        )}
      </div>
      {mutation.isError && <ErrorState error={mutation.error} />}
    </form>
  );
}
