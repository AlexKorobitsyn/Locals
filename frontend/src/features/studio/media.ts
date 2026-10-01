import { renew_access_token } from '../../api/client';
import { ApiError, response_error } from '../../api/errors';
import type { components } from '../../api/generated';
import { get_tokens } from '../../api/session';
import { BYTES_PER_MIB, PERCENT_TOTAL, UPLOAD_TIMEOUT_MS } from '../../app/constants';

export type UploadLimits = { image_max_bytes: number; audio_max_bytes: number };
export type MediaKind = 'image' | 'audio';
export const FILE_ACCEPT = { image: '.jpg,.jpeg,.png,.webp', audio: '.mp3,.flac,.wav' };
const EXTENSIONS = { image: ['jpg', 'jpeg', 'png', 'webp'], audio: ['mp3', 'flac', 'wav'] };
export function validate_file(file: File, kind: MediaKind, limits: UploadLimits) {
  if (!file.size) throw new ApiError(422, 'Файл пустой. Выберите другой.');
  if (!EXTENSIONS[kind].includes(file.name.split('.').at(-1)?.toLowerCase() || ''))
    throw new ApiError(
      415,
      kind === 'image'
        ? 'Для обложки подходят JPEG, PNG и WebP.'
        : 'Для аудио подходят MP3, FLAC и WAV.',
    );
  const maximum = kind === 'image' ? limits.image_max_bytes : limits.audio_max_bytes;
  if (file.size > maximum)
    throw new ApiError(413, `Максимальный размер: ${Math.floor(maximum / BYTES_PER_MIB)} МБ.`);
}

function send_file(
  file: File,
  kind: MediaKind,
  access_token: string,
  on_progress: (percent: number) => void,
  signal: AbortSignal,
) {
  return new Promise<{ status: number; data: unknown }>((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const abort = () => xhr.abort();
    if (signal.aborted) {
      reject(new DOMException('Upload cancelled', 'AbortError'));
      return;
    }
    signal.addEventListener('abort', abort, { once: true });
    const cleanup = () => signal.removeEventListener('abort', abort);
    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable)
        on_progress(Math.round((event.loaded * PERCENT_TOTAL) / event.total));
    };
    xhr.onload = () => {
      cleanup();
      resolve({ status: xhr.status, data: xhr.response });
    };
    xhr.onerror = () => {
      cleanup();
      reject(new ApiError(0, 'Соединение прервалось. Файл можно отправить ещё раз.'));
    };
    xhr.ontimeout = () => {
      cleanup();
      reject(new ApiError(0, 'Загрузка заняла слишком много времени. Попробуйте ещё раз.'));
    };
    xhr.onabort = () => {
      cleanup();
      reject(new DOMException('Upload cancelled', 'AbortError'));
    };
    xhr.open('POST', `/api/v1/media/${kind === 'image' ? 'images' : 'audio'}`);
    xhr.responseType = 'json';
    xhr.timeout = UPLOAD_TIMEOUT_MS;
    xhr.setRequestHeader('Authorization', `Bearer ${access_token}`);
    const body = new FormData();
    body.append('file', file);
    xhr.send(body);
  });
}

export async function upload_file(
  file: File,
  kind: MediaKind,
  limits: UploadLimits,
  on_progress: (percent: number) => void,
  signal: AbortSignal,
): Promise<components['schemas']['MediaOut']> {
  validate_file(file, kind, limits);
  const tokens = get_tokens();
  if (!tokens) throw new ApiError(401, 'Войдите, чтобы загрузить файл.');
  let result = await send_file(file, kind, tokens.access_token, on_progress, signal);
  if (result.status === 401 && get_tokens()?.session_id === tokens.session_id && !signal.aborted) {
    await renew_access_token();
    const renewed = get_tokens();
    if (!renewed || renewed.session_id !== tokens.session_id)
      throw new ApiError(401, 'Аккаунт изменился. Повторите загрузку.');
    on_progress(0);
    result = await send_file(file, kind, renewed.access_token, on_progress, signal);
  }
  if (signal.aborted) throw new DOMException('Upload cancelled', 'AbortError');
  if (get_tokens()?.session_id !== tokens.session_id)
    throw new ApiError(401, 'Аккаунт изменился. Повторите загрузку.');
  if (result.status < 200 || result.status >= 300) throw response_error(result.status, result.data);
  return result.data as components['schemas']['MediaOut'];
}
