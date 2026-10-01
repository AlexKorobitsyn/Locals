import { afterEach, describe, expect, it, vi } from 'vitest';
import { authenticated_fetch } from './client';
import { get_tokens, set_tokens } from './session';
import { response_error } from './errors';
import type { components } from './generated';

const tokens: components['schemas']['BrowserToken'] = {
  access_token: 'old-access',
  token_type: 'bearer',
  expires_in: 60,
  user_id: 1,
  session_id: 'first-session',
};
const renewed = { ...tokens, access_token: 'new-access' };
const request = () => new Request('http://localhost/api/v1/me');
afterEach(() => {
  set_tokens(null);
  vi.unstubAllGlobals();
});

describe('HTTP session', () => {
  it('rotates refresh once for concurrent and delayed 401 responses', async () => {
    set_tokens(tokens);
    let refresh_count = 0;
    const fetch_mock = vi.fn(async (input: RequestInfo | URL) => {
      const sent =
        input instanceof Request
          ? input
          : new Request(new URL(String(input), window.location.origin));
      if (sent.url.endsWith('/auth/browser/refresh')) {
        refresh_count += 1;
        await Promise.resolve();
        return Response.json(renewed);
      }
      return sent.headers.get('Authorization') === 'Bearer new-access'
        ? Response.json({ ok: true })
        : Response.json({ detail: 'expired' }, { status: 401 });
    });
    vi.stubGlobal('fetch', fetch_mock);
    const responses = await Promise.all([
      authenticated_fetch(request()),
      authenticated_fetch(request()),
      authenticated_fetch(request()),
    ]);
    expect(responses.map((response) => response.status)).toEqual([200, 200, 200]);
    expect(refresh_count).toBe(1);
    expect(get_tokens()?.access_token).toBe('new-access');
    const refreshed_request = fetch_mock.mock.calls
      .map(([input]) => input as Request)
      .find((sent) => sent.url.endsWith('/auth/browser/refresh'))!;
    expect(refreshed_request.credentials).toBe('same-origin');
    expect(refreshed_request.headers.get('X-CSRF-Protection')).toBe('1');
    expect(await refreshed_request.text()).toBe('');
  });

  it('clears a revoked session and does not loop', async () => {
    set_tokens(tokens);
    const fetch_mock = vi.fn(async (_input: RequestInfo | URL) =>
      Response.json({ detail: 'Invalid or expired credentials' }, { status: 401 }),
    );
    vi.stubGlobal('fetch', fetch_mock);
    await expect(authenticated_fetch(request())).rejects.toMatchObject({ status: 401 });
    expect(fetch_mock).toHaveBeenCalledTimes(2);
    expect(get_tokens()).toBeNull();
  });

  it('sends Bearer to logout without attaching it to login', async () => {
    set_tokens(tokens);
    const fetch_mock = vi.fn(
      async (_input: RequestInfo | URL) => new Response(null, { status: 204 }),
    );
    vi.stubGlobal('fetch', fetch_mock);
    await authenticated_fetch(
      new Request('http://localhost/api/v1/auth/logout', { method: 'POST' }),
    );
    await authenticated_fetch(
      new Request('http://localhost/api/v1/auth/login', { method: 'POST' }),
    );
    expect((fetch_mock.mock.calls[0]?.[0] as Request).headers.get('Authorization')).toBe(
      'Bearer old-access',
    );
    expect((fetch_mock.mock.calls[1]?.[0] as Request).headers.has('Authorization')).toBe(false);
  });

  it('does not repeat an old account request with a new account token', async () => {
    set_tokens(tokens);
    let resolve_request!: (response: Response) => void;
    const fetch_mock = vi.fn(
      () =>
        new Promise<Response>((resolve) => {
          resolve_request = resolve;
        }),
    );
    vi.stubGlobal('fetch', fetch_mock);
    const pending_request = authenticated_fetch(request());
    set_tokens(renewed);
    resolve_request(Response.json({ detail: 'expired' }, { status: 401 }));
    expect((await pending_request).status).toBe(401);
    expect(fetch_mock).toHaveBeenCalledTimes(1);
    expect(get_tokens()).toEqual(renewed);
  });

  it('does not resurrect a session after logout during refresh', async () => {
    set_tokens(tokens);
    let resolve_refresh!: (response: Response) => void;
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL) =>
        String(input instanceof Request ? input.url : input).endsWith('/auth/browser/refresh')
          ? new Promise<Response>((resolve) => {
              resolve_refresh = resolve;
            })
          : Response.json({ detail: 'expired' }, { status: 401 }),
      ),
    );
    const pending_request = authenticated_fetch(request());
    await vi.waitFor(() => expect(resolve_refresh).toBeDefined());
    set_tokens(null);
    resolve_refresh(Response.json(renewed));
    await pending_request;
    expect(get_tokens()).toBeNull();
  });
});

it('formats validation errors without exposing their input', () => {
  const error = response_error(422, {
    detail: [{ loc: ['body', 'password'], msg: 'bad', input: 'secret-password' }],
  });
  expect(error.field_errors).toEqual(['Пароль: недопустимое значение']);
  expect(JSON.stringify(error)).not.toContain('secret-password');
});
