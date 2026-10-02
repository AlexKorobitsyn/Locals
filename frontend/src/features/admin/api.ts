import { authenticated_fetch } from '../../api/client';
import { response_error } from '../../api/errors';

export async function admin_request<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
  const response = await authenticated_fetch(new URL('/api/v1' + path, window.location.origin), {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) throw response_error(response.status, await response.json());
  return (response.status === 204 ? undefined : await response.json()) as T;
}
