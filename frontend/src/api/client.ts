import create_client from 'openapi-fetch';
import type { components, paths } from './generated';
import { ApiError, response_error } from './errors';
import { get_tokens, get_session_version, replace_tokens, set_tokens } from './session';
import { HTTP_TIMEOUT_MS } from '../app/constants';

let pending_refresh: { version: number; promise: Promise<void> } | null = null;
let restoration: Promise<void> | null = null;

async function with_session_lock<T>(operation: () => Promise<T>): Promise<T> {
  return navigator.locks
    ? await navigator.locks.request('locals-auth', operation)
    : await operation();
}

async function browser_request(
  path: 'login' | 'refresh' | 'logout',
  body?: components['schemas']['LoginInput'],
) {
  const response = await fetch(
    new Request(new URL(`/api/v1/auth/browser/${path}`, window.location.origin), {
      method: 'POST',
      credentials: 'same-origin',
      headers: {
        'X-CSRF-Protection': '1',
        ...(body ? { 'Content-Type': 'application/json' } : {}),
      },
      body: body ? JSON.stringify(body) : undefined,
      cache: 'no-store',
      signal: AbortSignal.timeout(HTTP_TIMEOUT_MS),
    }),
  );
  if (!response.ok) throw response_error(response.status, await response.json());
  return response;
}

export async function login_browser(credentials: components['schemas']['LoginInput']) {
  await with_session_lock(async () => {
    const response = await browser_request('login', credentials);
    set_tokens(await response.json(), true);
  });
}

export async function logout_browser() {
  await with_session_lock(async () => {
    await browser_request('logout');
    set_tokens(null, true);
  });
}

export function restore_session() {
  if (!restoration)
    restoration = refresh_tokens().catch((error: unknown) => {
      if (!(error instanceof ApiError && error.status === 401)) {
        restoration = null;
        throw error;
      }
    });
  return restoration;
}

export async function renew_access_token() {
  await refresh_tokens();
}

async function refresh_tokens() {
  const current_tokens = get_tokens();
  const current_version = get_session_version();
  if (pending_refresh?.version === current_version) return pending_refresh.promise;
  const promise = with_session_lock(async () => {
    try {
      if (get_session_version() !== current_version) return;
      if (current_tokens && get_tokens()?.access_token !== current_tokens.access_token) return;
      const response = await browser_request('refresh');
      const renewed: components['schemas']['BrowserToken'] = await response.json();
      if (get_session_version() === current_version) {
        if (current_tokens && current_tokens.session_id === renewed.session_id)
          replace_tokens(renewed, true);
        else set_tokens(renewed, true);
      }
    } catch (error) {
      if (
        get_session_version() === current_version &&
        error instanceof ApiError &&
        error.status === 401
      )
        set_tokens(null, !!current_tokens);
      throw error;
    } finally {
      if (pending_refresh?.version === current_version) pending_refresh = null;
    }
  });
  pending_refresh = { version: current_version, promise };
  return promise;
}

export async function authenticated_fetch(input: RequestInfo | URL, init?: RequestInit) {
  const original = new Request(input, init);
  const current_tokens = get_tokens();
  const current_version = get_session_version();
  const is_auth_route =
    ['/api/v1/auth/login', '/api/v1/auth/register', '/api/v1/auth/refresh'].includes(
      new URL(original.url, window.location.origin).pathname,
    ) || new URL(original.url).pathname.startsWith('/api/v1/auth/browser/');
  const send = (access_token?: string) => {
    const headers = new Headers(original.headers);
    if (access_token && !is_auth_route) headers.set('Authorization', `Bearer ${access_token}`);
    const request = new Request(original.clone(), {
      headers,
      cache: 'no-store',
      signal: AbortSignal.any([original.signal, AbortSignal.timeout(HTTP_TIMEOUT_MS)]),
    });
    return fetch(request);
  };
  const response = await send(current_tokens?.access_token);
  if (
    response.status !== 401 ||
    !current_tokens ||
    is_auth_route ||
    get_session_version() !== current_version
  )
    return response;
  // Запоздавший 401 повторяется с уже обновлённым access без второй ротации.
  if (get_tokens()?.access_token === current_tokens.access_token) await refresh_tokens();
  if (get_session_version() !== current_version) return response;
  const latest_tokens = get_tokens();
  if (!latest_tokens) return response;
  const retried = await send(latest_tokens.access_token);
  if (retried.status === 401 && get_tokens() === latest_tokens) set_tokens(null, true);
  return retried;
}

export const api = create_client<paths>({
  baseUrl: window.location.origin,
  fetch: authenticated_fetch,
});

export function unwrap<T>(result: { data?: T; error?: unknown; response: Response }): T {
  if (!result.response.ok) throw response_error(result.response.status, result.error);
  return result.data as T;
}
