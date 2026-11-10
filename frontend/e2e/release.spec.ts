import { expect, test, type Page, type APIRequestContext } from '@playwright/test';
import { PAGE_LIMIT } from '../src/app/constants';

const SAMPLE_RATE = 8000;
const AUDIO_SECONDS = 12;
const SAMPLE_BYTES = 2;
const WAV_HEADER_BYTES = 44;
const COVER = Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAAQAAAAECAIAAAAmkwkpAAAAFElEQVR4nGOUU5ZjgAEmBiSAmwMAE5IAZ6J4hBEAAAAASUVORK5CYII=',
  'base64',
);
function wav_file() {
  const data_size = SAMPLE_RATE * AUDIO_SECONDS * SAMPLE_BYTES;
  const wav = Buffer.alloc(WAV_HEADER_BYTES + data_size);
  wav.write('RIFF', 0);
  wav.writeUInt32LE(wav.length - 8, 4);
  wav.write('WAVEfmt ', 8);
  wav.writeUInt32LE(16, 16);
  wav.writeUInt16LE(1, 20);
  wav.writeUInt16LE(1, 22);
  wav.writeUInt32LE(SAMPLE_RATE, 24);
  wav.writeUInt32LE(SAMPLE_RATE * SAMPLE_BYTES, 28);
  wav.writeUInt16LE(SAMPLE_BYTES, 32);
  wav.writeUInt16LE(16, 34);
  wav.write('data', 36);
  wav.writeUInt32LE(data_size, 40);
  return wav;
}
async function register(page: Page, name: string) {
  const credentials = {
    email: `release-${crypto.randomUUID()}@example.com`,
    password: `release-password-${crypto.randomUUID()}`,
  };
  await page.goto('/register');
  await page.getByLabel('Как вас зовут').fill(name);
  await page.getByLabel('Email', { exact: true }).fill(credentials.email);
  await page.getByLabel('Пароль', { exact: true }).fill(credentials.password);
  await page.getByRole('button', { name: 'Создать аккаунт' }).click();
  await expect(page.getByRole('heading', { name: 'Что вы слушаете?' })).toBeVisible();
  return credentials;
}
async function bearer(
  request: APIRequestContext,
  credentials: { email: string; password: string },
) {
  const response = await request.post('/api/v1/auth/login', { data: credentials });
  expect(response.ok()).toBe(true);
  return { Authorization: `Bearer ${(await response.json()).access_token}` };
}

test('studio lists server publications on another device with pagination and owner-only pickers', async ({
  page,
  browser,
  request,
}) => {
  const credentials = await register(page, 'Server Studio Author');
  const headers = await bearer(request, credentials);
  const suffix = crypto.randomUUID();
  const own_artists: { id: number; name: string }[] = [];
  for (let index = 0; index <= PAGE_LIMIT; index += 1) {
    const response = await request.post('/api/v1/artists', {
      headers,
      data: { name: `${String(index + 1).padStart(3, '0')} Artist ${suffix}` },
    });
    expect(response.status()).toBe(201);
    own_artists.push(await response.json());
  }
  const first_artist = own_artists[0]!;
  const last_artist = own_artists.at(-1)!;
  const album_title = `Album ${suffix}`;
  const track_title = `Track ${suffix}`;
  const album_response = await request.post('/api/v1/albums', {
    headers,
    data: { title: album_title, artist_ids: [first_artist.id] },
  });
  expect(album_response.status()).toBe(201);
  const album = await album_response.json();
  const track_response = await request.post('/api/v1/tracks', {
    headers,
    data: {
      title: track_title,
      duration: AUDIO_SECONDS,
      album_id: album.id,
      artist_ids: [first_artist.id],
    },
  });
  expect(track_response.status()).toBe(201);
  const foreign_credentials = {
    email: `foreign-${suffix}@example.com`,
    password: 'foreign-test-password',
  };
  const foreign_registration = await request.post('/api/v1/auth/register', {
    data: { ...foreign_credentials, display_name: 'Other Studio Author' },
  });
  expect(foreign_registration.status()).toBe(201);
  const foreign_headers = await bearer(request, foreign_credentials);
  const foreign_response = await request.post('/api/v1/artists', {
    headers: foreign_headers,
    data: { name: `Foreign Artist ${suffix}` },
  });
  expect(foreign_response.status()).toBe(201);
  const foreign_artist = await foreign_response.json();

  await page.goto('/studio?kind=artists&sort=name');
  await expect(page.locator('.publication-row')).toHaveCount(PAGE_LIMIT);
  await expect(page.getByRole('link', { name: first_artist.name, exact: true })).toBeVisible();
  await expect(page.getByRole('link', { name: foreign_artist.name, exact: true })).toHaveCount(0);
  await page
    .getByRole('navigation', { name: 'Страницы' })
    .getByRole('button', { name: 'Далее →' })
    .click();
  await expect(page.getByRole('link', { name: last_artist.name, exact: true })).toBeVisible();
  await expect(page.locator('.publication-row')).toHaveCount(1);
  await page.reload();
  await expect(page.getByRole('link', { name: last_artist.name, exact: true })).toBeVisible();
  const tabs = page.getByRole('navigation', { name: 'Мои публикации' });
  await tabs.getByRole('link', { name: 'Альбомы', exact: true }).click();
  await expect(page.getByRole('link', { name: album_title, exact: true })).toBeVisible();
  await tabs.getByRole('link', { name: 'Треки', exact: true }).click();
  await expect(page.getByRole('link', { name: track_title, exact: true })).toBeVisible();
  await page.getByRole('link', { name: `Редактировать ${track_title}`, exact: true }).click();
  await page.getByLabel('Название', { exact: true }).fill(`${track_title} Edited`);
  await page.getByRole('button', { name: 'Сохранить изменения', exact: true }).click();
  await expect(page).toHaveURL((url) => /^\/tracks\/\d+$/.test(url.pathname));
  await expect(
    page.getByRole('heading', { name: `${track_title} Edited`, exact: true }),
  ).toBeVisible();
  await page.goto('/studio');
  await page
    .getByRole('navigation', { name: 'Мои публикации' })
    .getByRole('link', { name: 'Треки', exact: true })
    .click();
  await expect(
    page.getByRole('link', { name: `${track_title} Edited`, exact: true }),
  ).toBeVisible();

  await page.goto('/studio/albums/new');
  const picker = page.getByRole('combobox', { name: 'Выбрать артиста', exact: true });
  await picker.click();
  await expect(page.getByRole('listbox').getByRole('option')).toHaveCount(PAGE_LIMIT + 1);
  await picker.press('Escape');
  await page.getByRole('button', { name: 'Показать ещё', exact: true }).click();
  await picker.click();
  await expect(page.getByRole('listbox').getByRole('option')).toHaveCount(own_artists.length + 1);
  await expect(page.getByRole('option', { name: foreign_artist.name, exact: true })).toHaveCount(0);
  await page.getByRole('option', { name: first_artist.name, exact: true }).click();
  await page.getByRole('button', { name: 'Добавить артиста', exact: true }).click();
  await expect(page.locator('.artist-selection')).toContainText(first_artist.name);

  const second_context = await browser.newContext({ baseURL: new URL(page.url()).origin });
  try {
    const second_page = await second_context.newPage();
    await second_page.goto('/login?next=%2Fstudio%3Fkind%3Dtracks');
    await second_page.getByLabel('Email', { exact: true }).fill(credentials.email);
    await second_page.getByLabel('Пароль', { exact: true }).fill(credentials.password);
    await second_page.getByRole('button', { name: 'Войти', exact: true }).click();
    await expect(
      second_page.getByRole('link', { name: `${track_title} Edited`, exact: true }),
    ).toBeVisible();
    expect(await second_page.evaluate(() => localStorage.length)).toBe(0);
    await second_page.getByRole('button', { name: 'Выйти', exact: true }).click();
    await second_page.goto('/login?next=%2Fstudio');
    await second_page.getByLabel('Email', { exact: true }).fill(foreign_credentials.email);
    await second_page.getByLabel('Пароль', { exact: true }).fill(foreign_credentials.password);
    await second_page.getByRole('button', { name: 'Войти', exact: true }).click();
    await expect(
      second_page.getByRole('link', { name: foreign_artist.name, exact: true }),
    ).toBeVisible();
    await expect(second_page.locator('.publication-row')).toHaveCount(1);
    await expect(
      second_page.getByRole('link', { name: first_artist.name, exact: true }),
    ).toHaveCount(0);
    await second_page.setViewportSize({ width: 390, height: 844 });
    expect(
      await second_page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
    ).toBe(true);
  } finally {
    await second_context.close();
  }
});

test.beforeEach(() =>
  test.skip(process.env.E2E_REAL_API !== 'true', 'Requires disposable FastAPI and PostgreSQL.'),
);

test('HttpOnly session survives reload and concurrent tabs; logout clears both', async ({
  page,
  context,
  request,
}) => {
  const credentials = await register(page, 'Persistent Listener');
  const cookies = await context.cookies('http://127.0.0.1:5173/api/v1/auth/browser/refresh');
  expect(cookies.find((cookie) => cookie.name === 'locals_refresh')).toMatchObject({
    httpOnly: true,
    sameSite: 'Lax',
    path: '/api/v1/auth/browser',
  });
  expect(await page.evaluate(() => document.cookie)).not.toContain('locals_refresh');
  await page.reload();
  await expect(page.getByRole('link', { name: 'Persistent Listener', exact: true })).toBeVisible();
  const second = await context.newPage();
  await second.goto('/studio');
  await expect(second.getByRole('heading', { name: 'Пусть услышат.' })).toBeVisible();
  await Promise.all([page.reload(), second.reload()]);
  await expect(page.getByRole('link', { name: 'Persistent Listener', exact: true })).toBeVisible();
  await expect(
    second.getByRole('link', { name: 'Persistent Listener', exact: true }),
  ).toBeVisible();
  const persisted = await page.evaluate(() =>
    [...Object.values(localStorage), ...Object.values(sessionStorage)].join(' '),
  );
  expect(persisted).not.toMatch(/access_token|refresh_token|eyJ/);
  const first_user = await request.get('/api/v1/me', {
    headers: await bearer(request, credentials),
  });
  const user_id = (await first_user.json()).id;
  await page.getByRole('button', { name: 'Выйти', exact: true }).click();
  await expect(
    page.getByRole('banner').getByRole('link', { name: 'Войти', exact: true }),
  ).toBeVisible();
  await expect(
    second.getByRole('banner').getByRole('link', { name: 'Войти', exact: true }),
  ).toBeVisible();
  expect((await context.cookies()).some((cookie) => cookie.name === 'locals_refresh')).toBe(false);
  await page.reload();
  await expect(
    page.getByRole('banner').getByRole('link', { name: 'Войти', exact: true }),
  ).toBeVisible();
  await page.goto(`/users/${user_id}`);
  await expect(page.getByRole('heading', { name: 'Persistent Listener' })).toBeVisible();
  await register(page, 'Replacement Listener');
  await expect(
    second.getByRole('banner').getByRole('link', { name: 'Replacement Listener', exact: true }),
  ).toBeVisible();
  await expect(
    second.getByRole('banner').getByRole('link', { name: 'Persistent Listener', exact: true }),
  ).toHaveCount(0);
});

test('studio uploads cover and playable WAV to MinIO; failed attach retries without duplicate', async ({
  page,
  request,
}) => {
  test.skip(process.env.E2E_MEDIA !== 'true', 'Requires configured real MinIO/S3.');
  const credentials = await register(page, 'Studio Author');
  const artist_name = `Release Artist ${crypto.randomUUID()}`;
  const album_name = `Release Album ${crypto.randomUUID()}`;
  const track_name = `Release Track ${crypto.randomUUID()}`;
  await page.goto('/studio/artists/new');
  await page.getByLabel('Имя артиста').fill(artist_name);
  await page.getByLabel('Об артисте').fill('Записано дома.');
  await page
    .getByLabel('Обложка', { exact: false })
    .setInputFiles({ name: 'cover.png', mimeType: 'image/png', buffer: COVER });
  await page.getByRole('button', { name: 'Создать артиста', exact: true }).click();
  await expect(page).toHaveURL((url) => /^\/artists\/\d+$/.test(url.pathname));
  await expect(page.getByRole('heading', { name: artist_name, exact: true })).toBeVisible();
  await page.getByRole('link', { name: 'Добавить альбом', exact: true }).click();
  await page.getByLabel('Название', { exact: true }).fill(album_name);
  await page.getByRole('button', { name: 'Создать альбом', exact: true }).click();
  await expect(page).toHaveURL((url) => /^\/albums\/\d+$/.test(url.pathname));
  await expect(page.getByRole('heading', { name: album_name, exact: true })).toBeVisible();
  await page.getByRole('link', { name: 'Загрузить трек', exact: true }).click();
  await page.getByLabel('Название', { exact: true }).fill(track_name);
  await page.getByLabel('Аудиофайл', { exact: false }).setInputFiles({
    name: 'bad.exe',
    mimeType: 'application/octet-stream',
    buffer: Buffer.from('invalid'),
  });
  await page.getByRole('button', { name: 'Опубликовать трек', exact: true }).click();
  await expect(page.getByText('Для аудио подходят MP3, FLAC и WAV.').first()).toBeVisible();
  await page
    .getByLabel('Аудиофайл', { exact: false })
    .setInputFiles({ name: 'audio.wav', mimeType: 'audio/wav', buffer: wav_file() });
  let track_posts = 0;
  let audio_uploads = 0;
  page.on('request', (entry) => {
    const path = new URL(entry.url()).pathname;
    if (entry.method() === 'POST' && path === '/api/v1/tracks') track_posts += 1;
    if (entry.method() === 'POST' && path === '/api/v1/media/audio') audio_uploads += 1;
  });
  await page.route('**/api/v1/media/audio', async (route) => {
    await route.fulfill({ status: 401, json: { detail: 'Invalid or expired credentials' } });
    await page.unroute('**/api/v1/media/audio');
  });
  await page.route('**/api/v1/tracks/*/audio', async (route) => {
    await route.fulfill({ status: 503, json: { detail: 'Temporary storage failure' } });
    await page.unroute('**/api/v1/tracks/*/audio');
  });
  await page.getByRole('button', { name: 'Опубликовать трек', exact: true }).click();
  await expect(page.getByText('Запись уже создана.', { exact: false })).toBeVisible();
  await page.getByRole('button', { name: 'Повторить подключение файлов' }).click();
  await expect(page).toHaveURL((url) => /^\/tracks\/\d+$/.test(url.pathname));
  await expect(page.getByRole('heading', { name: track_name, exact: true })).toBeVisible();
  expect(track_posts).toBe(1);
  expect(audio_uploads).toBe(2);
  const track_id = Number(new URL(page.url()).pathname.split('/').at(-1));
  const headers = await bearer(request, credentials);
  const details = await request.get(`/api/v1/tracks/${track_id}`, { headers });
  expect(await details.json()).toMatchObject({
    title: track_name,
    duration: AUDIO_SECONDS,
    album: { title: album_name },
  });
  const playback = await request.get(`/api/v1/tracks/${track_id}/playback`);
  const range = await request.get((await playback.json()).url, {
    headers: { Range: 'bytes=0-43', Origin: 'http://127.0.0.1:5173' },
  });
  expect(range.status()).toBe(206);
  expect(range.headers()['content-range']).toMatch(/^bytes 0-43\//);
  expect(range.headers()['access-control-allow-origin']).toBe('http://127.0.0.1:5173');
  await page.getByRole('button', { name: 'Слушать', exact: true }).click();
  await expect
    .poll(() => page.locator('audio').evaluate((audio: HTMLAudioElement) => audio.currentTime))
    .toBeGreaterThan(0);
  await page.getByRole('link', { name: 'События', exact: true }).click();
  await expect
    .poll(() => page.locator('audio').evaluate((audio: HTMLAudioElement) => !audio.paused))
    .toBe(true);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(`/studio/tracks/${track_id}`);
  await page.getByLabel('Название', { exact: true }).fill(`${track_name} Edited`);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(
    true,
  );
  await page.getByRole('button', { name: 'Сохранить изменения', exact: true }).click();
  await expect(page).toHaveURL(`/tracks/${track_id}`);
  await expect(
    page.getByRole('heading', { name: `${track_name} Edited`, exact: true }),
  ).toBeVisible();
});

test('venue, event filters and editing; following exposes venue activity in the feed', async ({
  page,
  browser,
  request,
}) => {
  const credentials = await register(page, 'Scene Author');
  const initial_headers = await bearer(request, credentials);
  const own_user = await (await request.get('/api/v1/me', { headers: initial_headers })).json();
  const administrator = await bearer(request, {
    email: process.env.E2E_ADMIN_EMAIL!,
    password: process.env.E2E_ADMIN_PASSWORD!,
  });
  expect(
    (
      await request.put(`/api/v1/admin/users/${own_user.id}/experience`, {
        headers: administrator,
        data: { tier: 3 },
      })
    ).status(),
  ).toBe(200);
  await page.goto('/login?next=/preferences');
  await page.getByLabel('Email', { exact: true }).fill(credentials.email);
  await page.getByLabel('Пароль', { exact: true }).fill(credentials.password);
  await page.getByRole('button', { name: 'Войти', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Что вы слушаете?' })).toBeVisible();
  const headers = await bearer(request, credentials);
  const city_response = await request.get('/api/v1/cities?q=Frontend%20City');
  const city = (await city_response.json()).items[0];
  expect(city).toBeTruthy();
  const venue_name = `Venue ${crypto.randomUUID()}`;
  const event_name = `Event ${crypto.randomUUID()}`;
  await page.goto('/venues/new');
  await page.getByLabel('Название', { exact: true }).fill(venue_name);
  await page.getByRole('combobox', { name: 'Город', exact: true }).click();
  await page.getByRole('option', { name: city.name, exact: true }).click();
  await page.getByLabel('Широта', { exact: true }).fill('56.83');
  await page.getByLabel('Долгота', { exact: true }).fill('60.60');
  await page.getByRole('button', { name: 'Создать площадку', exact: true }).click();
  await expect(page.getByRole('heading', { name: venue_name })).toBeVisible();
  const venue_id = Number(new URL(page.url()).pathname.split('/').at(-1));
  const listener_context = await browser.newContext({ baseURL: new URL(page.url()).origin });
  const listener = await listener_context.newPage();
  try {
    await register(listener, 'Scene Listener');
    await listener.goto(`/venues/${venue_id}`);
    await listener.getByRole('button', { name: 'Подписаться', exact: true }).click();
    await expect(listener.getByRole('button', { name: 'Отписаться', exact: true })).toBeVisible();
    await listener.goto('/following');
    await expect(listener.getByRole('heading', { name: venue_name })).toBeVisible();
    await page.getByRole('link', { name: 'Добавить событие здесь', exact: true }).click();
    await page.getByLabel('Название', { exact: true }).fill(event_name);
    await page.getByLabel('Начало', { exact: true }).fill('2027-06-01T20:00');
    await page.getByLabel('Окончание · необязательно').fill('2027-06-01T19:00');
    await page.getByRole('button', { name: 'Опубликовать событие', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'Новое событие.' })).toBeVisible();
    await page.getByLabel('Окончание · необязательно').fill('2027-06-01T23:00');
    await page.getByRole('button', { name: 'Опубликовать событие', exact: true }).click();
    await expect(page.getByRole('heading', { name: event_name })).toBeVisible();
    const event_id = Number(new URL(page.url()).pathname.split('/').at(-1));
    await listener.goto('/feed');
    await expect(listener.getByText('добавил событие', { exact: false })).toBeVisible();
    await listener.getByRole('link', { name: 'Открыть событие →' }).click();
    await expect(listener.getByRole('heading', { name: event_name })).toBeVisible();
    await expect(listener.getByRole('link', { name: 'Редактировать', exact: true })).toHaveCount(0);
    const own_only = await request.patch(`/api/v1/events/${event_id}`, {
      data: { name: 'Anonymous update' },
    });
    expect(own_only.status()).toBe(401);
    await page.getByRole('link', { name: 'Редактировать', exact: true }).click();
    await page.getByLabel('Описание').fill('Ночной сет.');
    await page.getByRole('button', { name: 'Сохранить изменения', exact: true }).click();
    await expect(page.getByText('Ночной сет.')).toBeVisible();
    await page.goto(
      `/events?city_id=${city.id}&starts_after=2027-06-01T00%3A00&starts_before=2027-06-02T00%3A00`,
    );
    await expect(page.getByRole('heading', { name: event_name })).toBeVisible();
    await page.getByLabel('С даты', { exact: true }).fill('2028-06-01T00:00');
    await expect(page.getByText('Проверьте даты:', { exact: false })).toBeVisible();
    await page.getByLabel('До даты', { exact: true }).fill('2028-06-02T00:00');
    await expect(page.getByRole('heading', { name: 'Ничего не найдено' })).toBeVisible();
    await page.goto(`/events/${event_id}`);
    await page.getByRole('button', { name: 'Удалить событие', exact: true }).click();
    await page.getByRole('button', { name: 'Подтвердить удаление' }).click();
    await expect(page.getByRole('heading', { name: 'После заката.' })).toBeVisible();
    expect((await request.get(`/api/v1/events/${event_id}`, { headers })).status()).toBe(404);
  } finally {
    await listener_context.close();
  }
});
