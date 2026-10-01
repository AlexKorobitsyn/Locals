import { Link, useLocation } from 'react-router';
import { useMutation } from '@tanstack/react-query';
import { Heart } from 'lucide-react';
import { api, unwrap } from '../../api/client';
import type { components } from '../../api/generated';
import { invalidate_music } from '../../app/query';
import { ErrorState } from '../../components/States';
import { use_auth } from '../auth/AuthProvider';

export function FavoriteButton({
  entity_type,
  entity_id,
  is_liked,
}: {
  entity_type: components['schemas']['FavoriteTarget'];
  entity_id: number;
  is_liked: boolean;
}) {
  const { user } = use_auth();
  const location = useLocation();
  const mutation = useMutation({
    mutationFn: async () =>
      is_liked
        ? unwrap(
            await api.DELETE('/api/v1/favorites/{entity_type}/{entity_id}', {
              params: { path: { entity_type, entity_id } },
            }),
          )
        : unwrap(await api.PUT('/api/v1/favorites', { body: { entity_type, entity_id } })),
    onSuccess: invalidate_music,
  });
  if (!user)
    return (
      <Link className="button" to={`/login?next=${encodeURIComponent(location.pathname)}`}>
        <Heart size={17} />
        Сохранить
      </Link>
    );
  return (
    <>
      <button
        className={`button ${is_liked ? 'liked' : ''}`}
        aria-pressed={is_liked}
        disabled={mutation.isPending}
        onClick={() => mutation.mutate()}
      >
        <Heart size={17} fill={is_liked ? 'currentColor' : 'none'} />
        {is_liked ? 'Сохранено' : 'Сохранить'}
      </button>
      {mutation.isError && <ErrorState error={mutation.error} />}
    </>
  );
}
