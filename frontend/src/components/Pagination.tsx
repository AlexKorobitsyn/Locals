import { PAGE_LIMIT } from '../app/constants';

export function Pagination({
  total,
  offset,
  on_change,
  limit = PAGE_LIMIT,
}: {
  total: number;
  offset: number;
  on_change: (offset: number) => void;
  limit?: number;
}) {
  if (total <= limit && offset === 0) return null;
  return (
    <nav className="pagination" aria-label="Страницы">
      <button
        className="button"
        disabled={offset === 0}
        onClick={() => on_change(Math.max(0, offset - limit))}
      >
        ← Назад
      </button>
      <span>
        {Math.floor(offset / limit) + 1} / {Math.max(1, Math.ceil(total / limit))}
      </span>
      <button
        className="button"
        disabled={offset + limit >= total}
        onClick={() => on_change(offset + limit)}
      >
        Далее →
      </button>
    </nav>
  );
}
