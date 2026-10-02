import { expect, test, type APIRequestContext, type Page } from '@playwright/test';

async function login(request: APIRequestContext, email: string, password: string) {
  const response = await request.post('/api/v1/auth/login', { data: { email, password } });
  expect(response.status()).toBe(200);
  return { Authorization: `Bearer ${(await response.json()).access_token}` };
}
async function browser_login(page: Page, email: string, password: string) {
  if (await page.getByRole('button', { name: 'Выйти', exact: true }).isVisible()) {
    await page.getByRole('button', { name: 'Выйти', exact: true }).click();
    await expect(
      page.getByRole('banner').getByRole('link', { name: 'Войти', exact: true }),
    ).toBeVisible();
  }
  await page.goto('/login?next=/preferences');
  await page.getByLabel('Email', { exact: true }).fill(email);
  await page.getByLabel('Пароль', { exact: true }).fill(password);
  await page.getByRole('button', { name: 'Войти', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Что вы слушаете?' })).toBeVisible();
}
test.beforeEach(() =>
  test.skip(process.env.E2E_REAL_API !== 'true', 'Requires a disposable backend.'),
);

test('newcomer proposes a venue, owner protects lyrics, admin assigns a level and verification on site', async ({
  page,
  request,
}) => {
  const suffix = crypto.randomUUID();
  const credentials = { email: `xp-e2e-${suffix}@example.com`, password: `xp-password-${suffix}` };
  const registration = await request.post('/api/v1/auth/register', {
    data: { ...credentials, display_name: `Organizer ${suffix}` },
  });
  expect(registration.status()).toBe(201);
  const user = await registration.json();
  const headers = await login(request, credentials.email, credentials.password);
  await browser_login(page, credentials.email, credentials.password);
  await page.goto('/progress');
  await expect(page.getByRole('heading', { name: /уровень 1: Новичок/ })).toBeVisible();
  await page.getByRole('link', { name: 'Предложить площадку', exact: true }).click();
  await page.getByLabel('Название', { exact: true }).fill(`Pending venue ${suffix}`);
  const cities = await (await request.get('/api/v1/cities?q=Frontend%20City')).json();
  await page.getByRole('combobox', { name: 'Город', exact: true }).click();
  await page.getByRole('option', { name: cities.items[0].name, exact: true }).click();
  await page.getByLabel('Широта', { exact: true }).fill('56.83');
  await page.getByLabel('Долгота', { exact: true }).fill('60.60');
  await page.getByRole('button', { name: 'Предложить площадку', exact: true }).click();
  await expect(
    page.getByText('Предложение ожидает принятия сообществом.', { exact: false }),
  ).toBeVisible();
  const venue_id = Number(new URL(page.url()).pathname.split('/').at(-1));
  expect((await request.get(`/api/v1/venues/${venue_id}`)).status()).toBe(404);
  await browser_login(page, process.env.E2E_ADMIN_EMAIL!, process.env.E2E_ADMIN_PASSWORD!);
  await page.goto('/admin?section=users');
  await page.getByLabel('Поиск по имени или email').fill(credentials.email);
  const card = page.locator('article').filter({ hasText: credentials.email });
  await card.getByRole('button', { name: 'Редактировать', exact: true }).click();
  await page.getByRole('combobox', { name: 'Уровень опыта', exact: true }).click();
  await page.getByRole('option', { name: '9 — Легенда', exact: true }).click();
  await expect(page.getByLabel('Подтверждённый организатор: публикация без очереди')).toBeChecked();
  await page.getByRole('button', { name: 'Сохранить', exact: true }).click();
  await page.getByRole('button', { name: 'Подтвердить', exact: true }).click();
  await expect(page.getByRole('heading', { name: /Аккаунт:/ })).not.toBeVisible();
  const fresh = await login(request, credentials.email, credentials.password);
  const current = await (await request.get('/api/v1/me', { headers: fresh })).json();
  expect(current.experience_points).toBe(25000);
  expect(current.scene_verified).toBe(true);
  expect(current.level).toBe('experienced');
  await browser_login(page, credentials.email, credentials.password);
  await page.goto('/progress');
  await expect(page.getByRole('heading', { name: /уровень 9: Легенда/ })).toBeVisible();
  await expect(page.getByText(/Подтверждённый организатор — публикация/)).toBeVisible();
  expect((await request.get('/api/v1/admin/users', { headers })).status()).toBe(401);
  expect((await request.get('/api/v1/admin/users', { headers: fresh })).status()).toBe(403);
  expect(user.id).toBeGreaterThan(0);
});

test('lyrics proposal is available to newcomers and owner accepts it on the site', async ({
  page,
  request,
}) => {
  const suffix = crypto.randomUUID();
  const owner = { email: `xp-owner-${suffix}@example.com`, password: `owner-password-${suffix}` };
  const contributor = {
    email: `xp-contributor-${suffix}@example.com`,
    password: `contributor-password-${suffix}`,
  };
  for (const [credentials, name] of [
    [owner, 'Lyrics author'],
    [contributor, 'Community helper'],
  ] as const)
    expect(
      (
        await request.post('/api/v1/auth/register', {
          data: { ...credentials, display_name: name },
        })
      ).status(),
    ).toBe(201);
  const own = await login(request, owner.email, owner.password);
  const artist = await (
    await request.post('/api/v1/artists', { headers: own, data: { name: `Band ${suffix}` } })
  ).json();
  const track_response = await request.post('/api/v1/tracks', {
    headers: own,
    data: {
      title: `Song ${suffix}`,
      duration: 120,
      artist_ids: [artist.id],
      lyrics: 'Owner version',
    },
  });
  expect(track_response.status()).toBe(201);
  const track = await track_response.json();
  await browser_login(page, contributor.email, contributor.password);
  await page.goto(`/tracks/${track.id}`);
  await page.getByRole('button', { name: 'Предложить исправление' }).click();
  await page.getByLabel('Предлагаемый текст').fill('A better community version');
  await page.getByRole('button', { name: 'Отправить на проверку' }).click();
  await expect(page.getByRole('status')).toContainText('Предложение опубликовано');
  expect((await (await request.get(`/api/v1/tracks/${track.id}`)).json()).lyrics).toBe(
    'Owner version',
  );
  await browser_login(page, owner.email, owner.password);
  await page.goto(`/contributions?target_type=track&target_id=${track.id}`);
  await expect(page.getByText(/Голоса помогают ему выбрать правку/)).toBeVisible();
  await page.getByRole('button', { name: 'Одобрить', exact: true }).click();
  await page.getByRole('button', { name: 'Подтвердить', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Открытых предложений пока нет' })).toBeVisible();
  expect((await (await request.get(`/api/v1/tracks/${track.id}`)).json()).lyrics).toBe(
    'A better community version',
  );
  await browser_login(page, contributor.email, contributor.password);
  await page.goto('/progress');
  await expect(page.getByRole('heading', { name: /20 XP · уровень 1/ })).toBeVisible();
  await expect(page.getByText(/Принятое предложение/)).toBeVisible();
});
