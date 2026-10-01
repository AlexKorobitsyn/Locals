import { useQuery } from '@tanstack/react-query';
import { all_genres } from '../api/catalog';
import { MAX_RELATIONS } from '../app/constants';
import { ErrorState } from './States';

export function GenrePicker({
  value,
  on_change,
}: {
  value: number[];
  on_change: (value: number[]) => void;
}) {
  const query = useQuery({ queryKey: ['genres'], queryFn: ({ signal }) => all_genres(signal) });
  return (
    <fieldset className="genre-picker">
      <legend>Жанры · необязательно</legend>
      {query.data?.map((genre) => (
        <label key={genre.id} className={value.includes(genre.id) ? 'genre-selected' : ''}>
          <input
            type="checkbox"
            checked={value.includes(genre.id)}
            disabled={!value.includes(genre.id) && value.length >= MAX_RELATIONS}
            onChange={(event) =>
              on_change(
                event.target.checked ? [...value, genre.id] : value.filter((id) => id !== genre.id),
              )
            }
          />
          {genre.name}
        </label>
      ))}
      {query.isPending && <small role="status">Загружаем жанры…</small>}
      {query.isError && <ErrorState error={query.error} retry={() => void query.refetch()} />}
      {query.data?.length === 0 && <small className="muted">Жанров в каталоге пока нет.</small>}
    </fieldset>
  );
}
