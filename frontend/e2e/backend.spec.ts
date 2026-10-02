import { expect, test } from '@playwright/test';

test('register, rate 4.5, review, Liked, playlist ordering and privacy against FastAPI', async ({
  page,
  request,
}) => {
  test.skip(
    process.env.E2E_REAL_API !== 'true',
    'Requires disposable PostgreSQL and FastAPI; see frontend/README.md.',
  );
  const unique_id = crypto.randomUUID();
  const first_title = `E2E First ${unique_id}`;
  const second_title = `E2E Second ${unique_id}`;
  const email = `e2e-${unique_id}@example.com`;
  const password = `e2e-password-${unique_id}`;
  await page.goto('/register');
  await page.getByLabel('Как вас зовут').fill('E2E Listener');
  await page.getByLabel('Email', { exact: true }).fill(email);
  await page.getByLabel('Пароль', { exact: true }).fill(password);
  await page.getByRole('button', { name: 'Создать аккаунт' }).click();
  await expect(page.getByRole('heading', { name: 'Что вы слушаете?' })).toBeVisible();
  await page.getByRole('checkbox', { name: 'Frontend Rock' }).check();
  await Promise.all([
    page.waitForResponse(
      (response) =>
        response.url().endsWith('/api/v1/me/favorite-genres') &&
        response.request().method() === 'PUT' &&
        response.ok(),
    ),
    page.getByRole('button', { name: 'Сохранить жанры', exact: true }).click(),
  ]);
  await expect(page.getByRole('checkbox', { name: 'Frontend Rock' })).toBeChecked();
  const login = await request.post('/api/v1/auth/login', { data: { email, password } });
  expect(login.ok()).toBe(true);
  const tokens = await login.json();
  const headers = { Authorization: `Bearer ${tokens.access_token}` };
  const preferences = await request.get('/api/v1/me/favorite-genres', { headers });
  expect((await preferences.json()).map((genre: { name: string }) => genre.name)).toContain(
    'Frontend Rock',
  );
  const artist_response = await request.post('/api/v1/artists', {
    headers,
    data: { name: 'E2E Artist' },
  });
  expect(artist_response.status()).toBe(201);
  const artist = await artist_response.json();
  for (const title of [first_title, second_title]) {
    const response = await request.post('/api/v1/tracks', {
      headers,
      data: { title, duration: 120, artist_ids: [artist.id] },
    });
    expect(response.status()).toBe(201);
  }
  await page.getByRole('link', { name: 'Треки', exact: true }).first().click();
  await page.getByRole('heading', { name: first_title }).getByRole('link').click();
  await page.getByRole('radio', { name: '4.5 из 5', exact: true }).check();
  await page.getByRole('button', { name: 'Оценить', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Ваша оценка: 4.5' })).toBeVisible();
  await page.getByLabel('Ваша рецензия').fill('Музыка для внимательного слушателя.');
  await page.getByRole('button', { name: 'Опубликовать рецензию' }).click();
  await expect(page.getByText('Музыка для внимательного слушателя.')).toBeVisible();
  await page.getByRole('button', { name: 'Сохранить', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Сохранено', exact: true })).toBeVisible();
  await page.getByRole('link', { name: 'Библиотека', exact: true }).click();
  await page.getByRole('heading', { name: 'Мне нравится' }).click();
  await expect(page.getByRole('link', { name: first_title, exact: true })).toBeVisible();
  await page.getByRole('link', { name: '← Библиотека' }).click();
  await page.getByLabel('Название', { exact: true }).fill('E2E Mix');
  await page.getByRole('button', { name: 'Создать плейлист' }).click();
  await expect(page.getByRole('heading', { name: 'E2E Mix', exact: true })).toBeVisible();
  const playlist_id = Number(new URL(page.url()).pathname.split('/').at(-1));
  for (const title of [first_title, second_title]) {
    await page.getByRole('link', { name: 'Треки', exact: true }).first().click();
    await page.getByRole('heading', { name: title }).getByRole('link').click();
    await page.getByRole('button', { name: 'Добавить в плейлист', exact: true }).click();
    await page.getByRole('combobox', { name: 'Плейлист', exact: true }).click();
    await page.getByRole('option', { name: 'E2E Mix', exact: true }).click();
    await page.getByRole('button', { name: 'Добавить трек', exact: true }).click();
    await expect(page.getByRole('status')).toHaveText('Трек добавлен.');
  }
  await page.getByRole('link', { name: 'Библиотека', exact: true }).click();
  await page.getByRole('heading', { name: 'E2E Mix' }).click();
  await page.getByRole('button', { name: `Поднять ${second_title}` }).click();
  await expect(page.locator('.track-row').first()).toContainText(second_title);
  const anonymous = await request.get(`/api/v1/playlists/${playlist_id}`);
  expect(anonymous.status()).toBe(404);
  await page.getByRole('link', { name: 'Треки', exact: true }).first().click();
  await page.getByRole('heading', { name: first_title }).getByRole('link').click();
  await expect(page.getByText('Музыка для внимательного слушателя.')).toBeVisible();
  await page.getByRole('button', { name: 'Удалить оценку', exact: true }).click();
  await page.getByRole('button', { name: 'Удалить оценку и рецензию' }).click();
  await expect(page.getByText('Музыка для внимательного слушателя.')).toHaveCount(0);
  await page.getByRole('button', { name: 'Выйти', exact: true }).click();
  await expect(page.getByRole('link', { name: 'Войти', exact: true })).toBeVisible();
});
