import { can_edit_public, can_moderate } from '../../app/permissions';
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { entity_detail, EntityPicker } from '../../components/EntityPicker';
import { MAX_RELATIONS } from '../../app/constants';
import { use_auth } from '../auth/AuthProvider';

export type ArtistSelection = { artist_id: number; name: string; role: string };
const ROLE_MAX_LENGTH = 64;
export function ArtistsField({
  value,
  on_change,
  with_roles = false,
}: {
  value: ArtistSelection[];
  on_change: (value: ArtistSelection[]) => void;
  with_roles?: boolean;
}) {
  const { user } = use_auth();
  const [selected_id, set_selected_id] = useState<number | null>(null);
  const query = useQuery({
    queryKey: ['catalog_picker', user?.id, 'artists', selected_id],
    enabled: !!selected_id,
    queryFn: ({ signal }) => entity_detail('artists', selected_id!, signal),
  });
  function add_artist() {
    if (
      !query.data ||
      !can_edit_public(query.data.is_owner, user?.level) ||
      !('name' in query.data)
    )
      return;
    on_change([...value, { artist_id: query.data.id, name: query.data.name, role: 'primary' }]);
    set_selected_id(null);
  }
  return (
    <div className="artists-field">
      <span className="form-legend">
        {with_roles ? 'Артисты и участники записи' : 'Артисты релиза'}
      </span>
      {value.map((artist, index) => (
        <div className="artist-selection" key={`${artist.artist_id}:${index}`}>
          <strong>{artist.name}</strong>
          {with_roles && (
            <label>
              Роль
              <input
                aria-label={`Роль: ${artist.name}`}
                value={artist.role === 'primary' ? 'Основной исполнитель' : artist.role}
                required
                maxLength={ROLE_MAX_LENGTH}
                onChange={(event) =>
                  on_change(
                    value.map((entry, entry_index) =>
                      entry_index === index
                        ? {
                            ...entry,
                            role:
                              event.target.value === 'Основной исполнитель'
                                ? 'primary'
                                : event.target.value,
                          }
                        : entry,
                    ),
                  )
                }
              />
            </label>
          )}
          <button
            className="text-button"
            type="button"
            aria-label={`Убрать артиста ${artist.name}`}
            onClick={() => on_change(value.filter((_, entry_index) => entry_index !== index))}
          >
            Убрать
          </button>
        </div>
      ))}
      <EntityPicker
        kind="artists"
        label="Выбрать артиста"
        value={selected_id}
        on_change={set_selected_id}
        owner_only={!can_moderate(user?.level)}
      />
      <button
        type="button"
        className="button small"
        disabled={
          !can_edit_public(query.data?.is_owner, user?.level) ||
          !selected_id ||
          value.some((entry) => entry.artist_id === selected_id) ||
          value.length >= MAX_RELATIONS
        }
        onClick={add_artist}
      >
        Добавить артиста
      </button>
      <small className="muted">
        Добавьте хотя бы одного своего артиста. Для участников можно указать роль в записи.
      </small>
    </div>
  );
}
