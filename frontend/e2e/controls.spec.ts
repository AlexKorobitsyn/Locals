import { expect, test } from '@playwright/test';

const artist = { id: 7, name: 'Автор трека' };
const track = {
  id: 1,
  title: 'Звёздный трек',
  duration: 120,
  artists: [artist],
  rating_avg: null,
  ratings_count: 0,
  my_rating: null as number | null,
};

test('dropdowns open in one click, support keyboard and show the artist in catalog and player', async ({
  page,
}) => {
  await page.route('**/api/v1/**', (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path === '/api/v1/auth/browser/refresh') return route.fulfill({ status: 401, json: {} });
    if (path === '/api/v1/tracks')
      return route.fulfill({ json: { items: [track], total: 1, limit: 20, offset: 0 } });
    return route.fulfill({ status: 404, json: {} });
  });
  await page.goto('/tracks');
  const picker = page.getByRole('combobox', { name: 'Сортировка', exact: true });
  await picker.click();
  await expect(page.getByRole('listbox')).toBeVisible();
  await page.getByRole('option', { name: 'По названию', exact: true }).click();
  await expect(page).toHaveURL(/sort=title/);
  await picker.press('Home');
  await picker.press('Enter');
  await expect(page).toHaveURL(/sort=-created_at/);
  await picker.click();
  await picker.press('Escape');
  await expect(picker).toHaveAttribute('aria-expanded', 'false');
  await picker.click();
  await page.getByRole('heading', { name: 'Треки.' }).click();
  await expect(picker).toHaveAttribute('aria-expanded', 'false');
  await expect(
    page.locator('.catalog-card').getByRole('link', { name: artist.name, exact: true }),
  ).toHaveAttribute('href', '/artists/7');
  await page.getByRole('button', { name: `Слушать ${track.title}` }).click();
  await expect(
    page
      .getByRole('region', { name: 'Управление воспроизведением' })
      .getByRole('link', { name: artist.name, exact: true }),
  ).toBeVisible();
  await page.getByRole('button', { name: 'Очередь воспроизведения', exact: true }).click();
  await expect(page.getByRole('complementary', { name: 'Очередь воспроизведения' })).toContainText(
    artist.name,
  );
  await page.getByRole('button', { name: 'Закрыть очередь' }).click();
  await page.setViewportSize({ width: 390, height: 844 });
  await picker.click();
  await page.getByRole('option', { name: 'По длительности', exact: true }).click();
  await expect(page).toHaveURL(/sort=duration/);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});

test('whole and half stars are selected and sent as numbers, including by keyboard', async ({
  page,
}) => {
  let my_rating: number | null = null;
  const saved: number[] = [];
  await page.route('**/api/v1/**', async (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path === '/api/v1/auth/browser/refresh')
      return route.fulfill({
        json: {
          access_token: 'browser-test-access',
          token_type: 'bearer',
          expires_in: 900,
          user_id: 10,
          session_id: '11111111-1111-4111-8111-111111111111',
        },
      });
    if (path === '/api/v1/me')
      return route.fulfill({ json: { id: 10, display_name: 'Слушатель', level: 'green' } });
    if (path === '/api/v1/tracks/1')
      return route.fulfill({ json: { ...track, my_rating, created_at: '2026-01-01T00:00:00Z' } });
    if (path === '/api/v1/reviews')
      return route.fulfill({ json: { items: [], total: 0, limit: 20, offset: 0 } });
    if (path === '/api/v1/ratings') {
      my_rating = route.request().postDataJSON().value;
      saved.push(my_rating!);
      return route.fulfill({ json: { target_type: 'track', target_id: 1, my_rating } });
    }
    return route.fulfill({ status: 404, json: {} });
  });
  await page.goto('/tracks/1');
  const group = page.getByRole('group', { name: 'Ваша оценка', exact: true });
  await expect(group.getByRole('radio')).toHaveCount(9);
  await expect(page.getByRole('button', { name: 'Оценить', exact: true })).toBeDisabled();
  await group.getByRole('radio', { name: '4.5 из 5', exact: true }).check();
  await page.getByRole('button', { name: 'Оценить', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Ваша оценка: 4.5' })).toBeVisible();
  await group.getByRole('radio', { name: '4.5 из 5', exact: true }).focus();
  await page.keyboard.press('ArrowRight');
  await expect(group.getByRole('radio', { name: '5 из 5', exact: true })).toBeChecked();
  await page.getByRole('button', { name: 'Изменить оценку', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Ваша оценка: 5', exact: true })).toBeVisible();
  expect(saved).toEqual([4.5, 5]);
  await page.setViewportSize({ width: 390, height: 844 });
  await group.getByRole('radio', { name: '1 из 5', exact: true }).check();
  await expect(group.getByRole('radio', { name: '1 из 5', exact: true })).toBeChecked();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});
