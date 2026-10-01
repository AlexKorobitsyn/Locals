import { expect, test } from '@playwright/test';

const SAMPLE_RATE = 8_000;
const AUDIO_SECONDS = 12;
const SAMPLE_BYTES = 2;
const WAV_HEADER_BYTES = 44;
function silent_wav() {
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

test('native audio plays, seeks with Range and survives route navigation', async ({ page }) => {
  const wav = silent_wav();
  let range_requested = false;
  let playback_requests = 0;
  await page.route('**/test-audio.wav', async (route) => {
    const range = route.request().headers().range;
    const match = range?.match(/^bytes=(\d+)-(\d*)$/);
    const start = Number(match?.[1] || 0);
    const end = match?.[2] ? Math.min(Number(match[2]), wav.length - 1) : wav.length - 1;
    range_requested ||= !!match;
    await route.fulfill({
      status: match ? 206 : 200,
      contentType: 'audio/wav',
      headers: {
        'Accept-Ranges': 'bytes',
        ...(match ? { 'Content-Range': `bytes ${start}-${end}/${wav.length}` } : {}),
      },
      body: wav.subarray(start, end + 1),
    });
  });
  await page.route('**/api/v1/**', (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path === '/api/v1/auth/browser/refresh')
      return route.fulfill({ status: 401, json: { detail: 'Invalid or expired credentials' } });
    if (path === '/api/v1/tracks/1/playback') {
      playback_requests += 1;
      return route.fulfill({
        json: {
          url: 'http://127.0.0.1:5173/test-audio.wav',
          expires_in: 300,
          duration: AUDIO_SECONDS,
          content_type: 'audio/wav',
        },
      });
    }
    if (path === '/api/v1/tracks')
      return route.fulfill({
        json: {
          items: [
            {
              id: 1,
              title: 'Audio track',
              duration: AUDIO_SECONDS,
              rating_avg: null,
              ratings_count: 0,
            },
          ],
          total: 1,
          offset: 0,
          limit: 20,
        },
      });
    if (path === '/api/v1/albums')
      return route.fulfill({ json: { items: [], total: 0, offset: 0, limit: 20 } });
    return route.fulfill({ status: 404, json: { detail: 'Not found' } });
  });
  await page.goto('/tracks');
  await page.getByRole('button', { name: 'Слушать Audio track', exact: true }).click();
  await expect
    .poll(() =>
      page
        .locator('audio')
        .evaluate((audio: HTMLAudioElement) => !audio.paused && audio.currentTime > 0),
    )
    .toBe(true);
  await page.getByRole('button', { name: 'Пауза', exact: true }).click();
  await page.getByRole('slider', { name: 'Позиция воспроизведения' }).fill('5');
  await expect
    .poll(() => page.locator('audio').evaluate((audio: HTMLAudioElement) => audio.currentTime))
    .toBe(5);
  await page.getByRole('button', { name: 'Воспроизвести', exact: true }).click();
  await page.getByRole('link', { name: 'Альбомы', exact: true }).first().click();
  await expect(page.getByRole('heading', { name: 'Альбомы.' })).toBeVisible();
  await expect
    .poll(() =>
      page
        .locator('audio')
        .evaluate((audio: HTMLAudioElement) => !audio.paused && audio.currentTime > 5),
    )
    .toBe(true);
  expect(playback_requests).toBe(1);
  expect(range_requested).toBe(true);
});
