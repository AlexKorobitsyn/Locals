import { useQuery } from '@tanstack/react-query';
import { Link, useParams } from 'react-router';
import { can_moderate } from '../../app/permissions';
import { api, unwrap } from '../../api/client';
import { ApiError } from '../../api/errors';
import { parse_id } from '../../app/constants';
import { Cover } from '../../components/Cover';
import { ErrorState, LoadingState } from '../../components/States';
import { use_auth } from '../auth/AuthProvider';
import { ImageUpload } from '../studio/ImageUpload';
import { FollowButton } from './FollowButton';

export function ProfilePage() {
  const { user } = use_auth();
  const id = parse_id(useParams().id);
  const query = useQuery({
    queryKey: ['profile', user?.id, id],
    enabled: !!id,
    queryFn: async ({ signal }) =>
      unwrap(
        await api.GET('/api/v1/users/{user_id}', { params: { path: { user_id: id! } }, signal }),
      ),
  });
  if (!id) return <ErrorState error={new ApiError(404, 'Такого профиля нет.')} />;
  if (query.isPending) return <LoadingState />;
  if (query.isError) return <ErrorState error={query.error} retry={() => void query.refetch()} />;
  const profile = query.data;
  return (
    <>
      <div className="detail-hero artist-hero">
        <Cover large url={profile.avatar_url} name={profile.display_name} />
        <div>
          <span className="eyebrow">
            {profile.type === 'artist' ? 'АВТОР' : 'СЛУШАТЕЛЬ'}
            {profile.city ? ` · ${profile.city.name}` : ''}
          </span>
          <h1>{profile.display_name}</h1>
          <p className="eyebrow">
            {profile.level_name} · уровень {profile.experience_level} · {profile.experience_points}{' '}
            XP
          </p>
          {profile.scene_verified && <p>Подтверждённый организатор</p>}
          {can_moderate(user?.level) && (
            <Link className="button" to="/admin?section=profiles">
              Редактировать публичные профили
            </Link>
          )}
          <p className="muted">
            {profile.followers_count || 0} подписчиков · {profile.following_count || 0} подписок
          </p>
          <div className="actions">
            <FollowButton
              target_type="user"
              target_id={id}
              followed={profile.is_followed_by_me || false}
            />
            {user?.id === id && (
              <>
                <Link className="button primary" to="/studio">
                  Моя студия
                </Link>
                <Link className="button" to="/following">
                  Мои подписки
                </Link>
                <Link className="button" to="/preferences">
                  Мой вкус
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
      {profile.bio && (
        <section className="panel">
          <h2>О себе</h2>
          <p className="preserve-lines">{profile.bio}</p>
        </section>
      )}
      {user?.id === id && <ImageUpload key={id} target_type="user" target_id={id} />}
    </>
  );
}
