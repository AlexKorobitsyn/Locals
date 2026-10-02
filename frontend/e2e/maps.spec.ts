import { expect, test } from '@playwright/test';
import type { components } from '../src/api/generated';

const venue: components['schemas']['VenueRatedShort'] = {
  id: 1,
  name: 'Map Club',
  publication_status: 'published',
  city: { id: 1, name: 'Map City' },
  lat: 56.83,
  lng: 60.6,
  rating_avg: null,
  ratings_count: 0,
  likes_count: 0,
  is_liked_by_me: false,
};
const event: components['schemas']['EventOut'] = {
  id: 2,
  name: 'Map Concert',
  publication_status: 'published',
  venue,
  city: venue.city,
  lat: venue.lat,
  lng: venue.lng,
  starts_at: '2099-10-10T18:00:00Z',
  is_owner: false,
  likes_count: 0,
  is_liked_by_me: false,
  attendees_count: 0,
  is_going_by_me: false,
};

test.beforeEach(async ({ page }) => {
  await page.route('https://tile.openstreetmap.org/**', (route) =>
    route.fulfill({
      contentType: 'image/png',
      body: Buffer.from(
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aOc8AAAAASUVORK5CYII=',
        'base64',
      ),
    }),
  );
});

test('map highlights venues with events, opens their agenda and supports mobile navigation', async ({
  page,
}) => {
  await page.route('**/api/v1/**', async (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path.startsWith('/api/v1/auth/'))
      return route.fulfill({ status: 401, json: { detail: 'Invalid credentials' } });
    if (path === '/api/v1/cities')
      return route.fulfill({
        json: {
          items: [
            {
              ...venue.city,
              country: 'RU',
              lat: venue.lat,
              lng: venue.lng,
              timezone: 'Asia/Yekaterinburg',
            },
          ],
          total: 1,
          limit: 20,
          offset: 0,
        },
      });
    if (path === '/api/v1/cities/1')
      return route.fulfill({
        json: {
          ...venue.city,
          country: 'RU',
          lat: venue.lat,
          lng: venue.lng,
          timezone: 'Asia/Yekaterinburg',
        },
      });
    if (path === '/api/v1/event-types')
      return route.fulfill({ json: [{ id: 1, name: 'Concert', slug: 'concert' }] });
    if (path === '/api/v1/venues')
      return route.fulfill({ json: { items: [venue], total: 1, limit: 100, offset: 0 } });
    if (path === '/api/v1/events')
      return route.fulfill({ json: { items: [event], total: 1, limit: 100, offset: 0 } });
    return route.fulfill({ status: 404, json: { detail: 'Not found' } });
  });
  await page.goto('/map?city_id=1');
  await expect(page.getByRole('heading', { name: 'Карта сцены.' })).toBeVisible();
  await page.getByRole('button', { name: 'Map Club · 1 событий', exact: true }).click();
  await expect(page.locator('.leaflet-popup')).toContainText('Map Club');
  await expect(
    page
      .getByRole('region', { name: 'Выбранное место' })
      .getByRole('link', { name: 'Map Concert' }),
  ).toBeVisible();
  await expect(page.getByRole('link', { name: 'Афиша площадки', exact: true })).toHaveAttribute(
    'href',
    '/events?venue_id=1',
  );
  await page.getByLabel('Показывать события').uncheck();
  await expect(page.locator('.scene-marker-active_venue')).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Map Club', exact: true })).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(
    true,
  );
  await page.getByRole('button', { name: 'Открыть меню' }).click();
  await expect(
    page
      .getByRole('navigation', { name: 'Основная навигация' })
      .getByRole('link', { name: 'Карта', exact: true }),
  ).toBeVisible();
});

test('newcomer binds an event by clicking a venue and picks coordinates for a venue against FastAPI', async ({
  page,
  request,
}) => {
  test.skip(process.env.E2E_REAL_API !== 'true', 'Requires a disposable backend');
  const admin_login = await request.post('/api/v1/auth/login', {
    data: { email: process.env.E2E_ADMIN_EMAIL, password: process.env.E2E_ADMIN_PASSWORD },
  });
  expect(admin_login.status()).toBe(200);
  const admin_headers = { Authorization: `Bearer ${(await admin_login.json()).access_token}` };
  const city = (await (await request.get('/api/v1/cities?q=Frontend%20City')).json()).items[0];
  const venue_name = `Map Venue ${crypto.randomUUID()}`;
  const venue_response = await request.post('/api/v1/venues', {
    headers: admin_headers,
    data: { name: venue_name, city_id: city.id, lat: city.lat + 0.02, lng: city.lng + 0.03 },
  });
  expect(venue_response.status()).toBe(201);
  const created_venue = await venue_response.json();
  const credentials = {
    email: `map-${crypto.randomUUID()}@example.com`,
    password: 'map-test-password-long',
  };
  expect(
    (
      await request.post('/api/v1/auth/register', {
        data: { ...credentials, display_name: 'Map Newcomer' },
      })
    ).status(),
  ).toBe(201);
  await page.goto('/login?next=/events/new');
  await page.getByLabel('Email', { exact: true }).fill(credentials.email);
  await page.getByLabel('Пароль', { exact: true }).fill(credentials.password);
  await page.getByRole('button', { name: 'Войти', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Новое событие.' })).toBeVisible();
  await page.getByRole('combobox', { name: 'Город', exact: true }).selectOption(String(city.id));
  await page.getByRole('button', { name: venue_name, exact: true }).click();
  await expect(
    page.getByText('Место события берётся из площадки.', { exact: false }),
  ).toBeVisible();
  await expect(page.getByRole('combobox', { name: 'Площадка', exact: true })).toHaveValue(
    String(created_venue.id),
  );
  const event_name = `Bound event ${crypto.randomUUID()}`;
  await page.getByLabel('Название', { exact: true }).fill(event_name);
  await page.getByLabel('Начало', { exact: true }).fill('2027-06-01T20:00');
  const saved = page.waitForResponse(
    (response) =>
      response.request().method() === 'POST' &&
      new URL(response.url()).pathname === '/api/v1/events',
  );
  await page.getByRole('button', { name: 'Предложить событие', exact: true }).click();
  const saved_event = await (await saved).json();
  expect(saved_event.venue.id).toBe(created_venue.id);
  expect(saved_event.lat).toBe(created_venue.lat);
  expect(saved_event.lng).toBe(created_venue.lng);
  expect(saved_event.publication_status).toBe('pending');
  await expect(page.getByRole('heading', { name: event_name })).toBeVisible();
  expect((await request.get(`/api/v1/events/${saved_event.id}`)).status()).toBe(404);
  await page.goto('/venues/new');
  await page.getByLabel('Название', { exact: true }).fill(`New map venue ${crypto.randomUUID()}`);
  await page.getByRole('combobox', { name: 'Город', exact: true }).selectOption(String(city.id));
  await page
    .getByRole('region', { name: 'Выбор места площадки' })
    .click({ position: { x: 180, y: 110 } });
  await expect(page.getByLabel('Широта', { exact: true })).not.toHaveValue('');
  await expect(page.getByLabel('Долгота', { exact: true })).not.toHaveValue('');
  const venue_saved = page.waitForResponse(
    (response) =>
      response.request().method() === 'POST' &&
      new URL(response.url()).pathname === '/api/v1/venues',
  );
  await page.getByRole('button', { name: 'Предложить площадку', exact: true }).click();
  expect((await venue_saved).status()).toBe(201);
  await expect(
    page.getByText('Предложение ожидает принятия сообществом.', { exact: false }),
  ).toBeVisible();
});
