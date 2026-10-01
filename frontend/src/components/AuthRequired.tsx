import type { ReactNode } from 'react';
import { Link, useLocation } from 'react-router';
import { use_auth } from '../features/auth/AuthProvider';
import { ErrorState, LoadingState } from './States';

export function AuthRequired({ children }: { children: ReactNode }) {
  const { user, is_loading, error } = use_auth();
  const location = useLocation();
  if (is_loading) return <LoadingState />;
  if (!user)
    return (
      <div className="panel">
        <h1>Войдите в Locals</h1>
        <p className="muted">
          Публикуйте музыку, собирайте свою сцену и следите за теми, кто вам близок.
        </p>
        {!!error && <ErrorState error={error} />}
        <Link
          className="button primary"
          to={`/login?next=${encodeURIComponent(location.pathname + location.search)}`}
        >
          Войти
        </Link>
      </div>
    );
  return children;
}
