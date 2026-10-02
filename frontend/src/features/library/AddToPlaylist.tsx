import { Select } from '../../components/Select';
import { useState } from 'react';
import { Link } from 'react-router';
import { useMutation, useQuery } from '@tanstack/react-query';
import { api, unwrap } from '../../api/client';
import { invalidate_music } from '../../app/query';
import { EmptyState, ErrorState, LoadingState } from '../../components/States';
import { use_auth } from '../auth/AuthProvider';
import { all_own_playlists } from './api';

export function AddToPlaylist({ track_id }: { track_id: number }) {
  const { user } = use_auth();
  const [is_open, set_is_open] = useState(false);
  const [playlist_id, set_playlist_id] = useState('');
  const query = useQuery({
    queryKey: ['library', user?.id, 'all_own'],
    enabled: !!user && is_open,
    queryFn: ({ signal }) => all_own_playlists(signal),
  });
  const mutation = useMutation({
    mutationFn: async () =>
      unwrap(
        await api.POST('/api/v1/playlists/{playlist_id}/tracks', {
          params: { path: { playlist_id: Number(playlist_id) } },
          body: { track_id },
        }),
      ),
    onSuccess: invalidate_music,
  });
  if (!user) return null;
  const playlists = query.data?.filter((playlist) => playlist.kind === 'custom');
  return (
    <div className="add-to-playlist">
      <button className="text-button" onClick={() => set_is_open(!is_open)} aria-expanded={is_open}>
        Добавить в плейлист
      </button>
      {is_open && (
        <div className="panel">
          {query.isPending ? (
            <LoadingState />
          ) : query.isError ? (
            <ErrorState error={query.error} retry={() => void query.refetch()} />
          ) : !playlists?.length ? (
            <>
              <EmptyState
                title="Создайте первую подборку"
                description="Треки можно добавлять в свои обычные плейлисты."
              />
              <Link to="/library">Открыть библиотеку</Link>
            </>
          ) : (
            <div className="actions">
              <label>
                Плейлист
                <Select
                  label="Плейлист"
                  value={playlist_id}
                  on_change={(next_value) => set_playlist_id(next_value)}
                >
                  <option value="">Выберите</option>
                  {playlists.map((playlist) => (
                    <option key={playlist.id} value={playlist.id}>
                      {playlist.name}
                    </option>
                  ))}
                </Select>
              </label>
              <button
                className="button"
                disabled={!playlist_id || mutation.isPending}
                onClick={() => mutation.mutate()}
              >
                Добавить трек
              </button>
            </div>
          )}
          {mutation.isError && <ErrorState error={mutation.error} />}
          {mutation.isSuccess && <p role="status">Трек добавлен.</p>}
        </div>
      )}
    </div>
  );
}
