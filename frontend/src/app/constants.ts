export const PAGE_LIMIT = 20;
export const MAX_PAGE_LIMIT = 100;
export const QUERY_STALE_MS = 30_000;
export const QUERY_RETRY_COUNT = 1;
export const HTTP_TIMEOUT_MS = 20_000;
export const SECONDS_PER_MINUTE = 60;
export const MS_PER_SECOND = 1000;
export const DEFAULT_VOLUME = 0.7;
export const VOLUME_STEP = 0.05;
export const MAX_PLAYBACK_REFRESHES = 1;
export const RATING_VALUES = [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5] as const;
export const PASSWORD_MIN_LENGTH = 8;
export const PASSWORD_MAX_LENGTH = 128;
export const NAME_MAX_LENGTH = 255;
export const REVIEW_MAX_LENGTH = 50_000;
export const DESCRIPTION_MAX_LENGTH = 10_000;
export const LYRICS_MAX_LENGTH = 100_000;
export const MAX_RELATIONS = 100;
export const MAX_DATABASE_INTEGER = 2_147_483_647;
export const CITY_SEARCH_DELAY_MS = 250;
export const UPLOAD_TIMEOUT_MS = 10 * 60 * MS_PER_SECOND;
export const PERCENT_TOTAL = 100;
export const DEFAULT_IMAGE_MAX_BYTES = 10 * 1024 * 1024;
export const DEFAULT_AUDIO_MAX_BYTES = 100 * 1024 * 1024;
export const BYTES_PER_MIB = 1024 * 1024;
export const LATITUDE_MIN = -90;
export const LATITUDE_MAX = 90;
export const LONGITUDE_MIN = -180;
export const LONGITUDE_MAX = 180;

export function format_datetime(value: string, timezone?: string) {
  return new Intl.DateTimeFormat('ru-RU', {
    dateStyle: 'medium',
    timeStyle: 'short',
    ...(timezone ? { timeZone: timezone } : {}),
  }).format(new Date(value));
}

export function datetime_input(value?: string | null) {
  if (!value) return '';
  const date = new Date(value);
  const pad = (part: number) => String(part).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

export function format_duration(seconds: number) {
  const safe_seconds = Number.isFinite(seconds) ? Math.max(0, Math.floor(seconds)) : 0;
  return `${Math.floor(safe_seconds / SECONDS_PER_MINUTE)}:${String(safe_seconds % SECONDS_PER_MINUTE).padStart(2, '0')}`;
}

export function parse_id(value: string | undefined) {
  return value && /^[1-9]\d*$/.test(value) && Number.isSafeInteger(Number(value))
    ? Number(value)
    : null;
}
