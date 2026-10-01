import { useMutation } from '@tanstack/react-query';
import { Link, useLocation } from 'react-router';
import { UserPlus, Check } from 'lucide-react';
import { api, unwrap } from '../../api/client';
import type { components } from '../../api/generated';
import { invalidate_music } from '../../app/query';
import { ErrorState } from '../../components/States';
import { use_auth } from '../auth/AuthProvider';

export function FollowButton({
  target_type,
  target_id,
  followed,
}: {
  target_type: components['schemas']['FollowTarget'];
  target_id: number;
  followed: boolean;
}) {
  const { user } = use_auth();
  const location = useLocation();
  const mutation = useMutation({
    mutationFn: async () =>
      followed
        ? unwrap(
            await api.DELETE('/api/v1/follows/{target_type}/{target_id}', {
              params: { path: { target_type, target_id } },
            }),
          )
        : unwrap(await api.PUT('/api/v1/follows', { body: { target_type, target_id } })),
    onSuccess: invalidate_music,
  });
  if (target_type === 'user' && user?.id === target_id) return null;
  if (!user)
    return (
      <Link className="button" to={`/login?next=${encodeURIComponent(location.pathname)}`}>
        <UserPlus size={17} />
        Подписаться
      </Link>
    );
  return (
    <>
      <button
        className={`button ${followed ? 'liked' : ''}`}
        aria-pressed={followed}
        disabled={mutation.isPending}
        onClick={() => mutation.mutate()}
      >
        {followed ? <Check size={17} /> : <UserPlus size={17} />}
        {followed ? 'Отписаться' : 'Подписаться'}
      </button>
      {mutation.isError && <ErrorState error={mutation.error} />}
    </>
  );
}
