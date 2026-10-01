import { expect, test } from '@playwright/test';
import type { components } from '../src/api/generated';

test.beforeEach(async ({ page }) => {
  await page.route('**/api/v1/auth/browser/refresh', (route) =>
    route.fulfill({ status: 401, json: { detail: 'Invalid or expired credentials' } }),
  );
});

const track: components['schemas']['TrackRatedShort'] = {
  id: 1,
  title: 'Первый трек',
  duration: 120,
  ratings_count: 3,
  likes_count: 0,
  is_liked_by_me: false,
  rating_avg: 3.2,
};
test('catalog, details and missing audio use the real contract shape', async ({ page }) => {
  await page.route('**/api/v1/**', async (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path === '/api/v1/auth/browser/refresh')
      return route.fulfill({ status: 401, json: { detail: 'Invalid or expired credentials' } });
    if (path === '/api/v1/tracks')
      return route.fulfill({ json: { items: [track], total: 1, limit: 20, offset: 0 } });
    if (path === '/api/v1/tracks/1')
      return route.fulfill({
        json: {
          ...track,
          created_at: '2026-01-01T00:00:00Z',
          artists: [{ id: 2, name: 'Артист' }],
          album: { id: 3, title: 'Альбом' },
          audio_media_id: null,
        },
      });
    if (path === '/api/v1/reviews')
      return route.fulfill({ json: { items: [], total: 0, limit: 20, offset: 0 } });
    return route.fulfill({ status: 404, json: { detail: 'Not found' } });
  });
  await page.goto('/tracks');
  await expect(page.getByRole('heading', { name: 'Треки.' })).toBeVisible();
  await page.getByRole('heading', { name: 'Первый трек' }).getByRole('link').click();
  await expect(page.getByRole('heading', { name: 'Первый трек' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Слушать', exact: true })).toBeDisabled();
  await expect(page.getByText('Аудио пока не загружено.', { exact: false })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Альбом', exact: true })).toHaveAttribute(
    'href',
    '/albums/3',
  );
});

for (const status of [401, 403, 404, 422])
  test(`catalog displays HTTP ${status}`, async ({ page }) => {
    await page.route('**/api/v1/tracks*', (route) =>
      route.fulfill({ status, json: { detail: 'test' } }),
    );
    await page.goto('/tracks');
    await expect(page.getByRole('alert')).toContainText(`Ошибка ${status}`);
  });

test('mobile navigation is available without horizontal overflow', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.route('**/api/v1/tracks*', (route) =>
    route.fulfill({ json: { items: [], total: 0, limit: 20, offset: 0 } }),
  );
  await page.goto('/tracks');
  await page.getByRole('button', { name: 'Открыть меню' }).click();
  await expect(page.getByRole('navigation', { name: 'Основная навигация' })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(
    true,
  );
});
