import { useState, type FormEvent } from 'react';
import { Link, Navigate, useNavigate, useSearchParams } from 'react-router';
import { useMutation } from '@tanstack/react-query';
import { api, login_browser, unwrap } from '../../api/client';
import { query_client } from '../../app/query';
import { NAME_MAX_LENGTH, PASSWORD_MAX_LENGTH, PASSWORD_MIN_LENGTH } from '../../app/constants';
import { ErrorState, LoadingState } from '../../components/States';
import { use_auth } from './AuthProvider';

export function AuthPage({ register = false }: { register?: boolean }) {
  const { user, is_loading } = use_auth();
  const navigate = useNavigate();
  const [search_params] = useSearchParams();
  const [email, set_email] = useState('');
  const [password, set_password] = useState('');
  const [display_name, set_display_name] = useState('');
  const requested_path = search_params.get('next');
  const next_path =
    requested_path?.startsWith('/') && !requested_path.startsWith('//')
      ? requested_path
      : register
        ? '/preferences'
        : '/tracks';
  const mutation = useMutation({
    mutationFn: async () => {
      const credentials = { email: email.trim(), password };
      if (register)
        unwrap(
          await api.POST('/api/v1/auth/register', {
            body: { ...credentials, display_name: display_name.trim() },
          }),
        );
      await query_client.cancelQueries();
      query_client.clear();
      await login_browser(credentials);
      set_password('');
      navigate(next_path, { replace: true });
    },
  });
  if (is_loading) return <LoadingState />;
  if (user) return <Navigate to={next_path} replace />;
  function submit(event: FormEvent) {
    event.preventDefault();
    mutation.mutate();
  }
  return (
    <div className="auth-page">
      <span className="eyebrow">ВАША МУЗЫКА. ВАШЕ МНЕНИЕ.</span>
      <h1>{register ? 'Найдите свой звук' : 'С возвращением'}</h1>
      <p className="muted">Оценивайте музыку и открывайте то, что близко вам.</p>
      <form className="panel form" onSubmit={submit}>
        {register && (
          <label>
            Как вас зовут
            <input
              value={display_name}
              onChange={(event) => set_display_name(event.target.value)}
              required
              maxLength={NAME_MAX_LENGTH}
              autoComplete="nickname"
            />
          </label>
        )}
        <label>
          Email
          <input
            type="email"
            value={email}
            onChange={(event) => set_email(event.target.value)}
            autoComplete="email"
            required
          />
        </label>
        <label>
          Пароль
          <input
            type="password"
            value={password}
            onChange={(event) => set_password(event.target.value)}
            autoComplete={register ? 'new-password' : 'current-password'}
            required
            minLength={register ? PASSWORD_MIN_LENGTH : undefined}
            maxLength={PASSWORD_MAX_LENGTH}
          />
        </label>
        {mutation.isError && <ErrorState error={mutation.error} />}
        <button className="button primary" disabled={mutation.isPending}>
          {mutation.isPending ? 'Подождите…' : register ? 'Создать аккаунт' : 'Войти'}
        </button>
        <p className="muted">
          {register ? 'Уже есть аккаунт?' : 'Первый раз здесь?'}{' '}
          <Link
            to={`${register ? '/login' : '/register'}${requested_path ? `?next=${encodeURIComponent(next_path)}` : ''}`}
          >
            {register ? 'Войти' : 'Зарегистрироваться'}
          </Link>
        </p>
      </form>
    </div>
  );
}
