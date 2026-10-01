import { useEffect, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ApiError } from '../../api/errors';
import { BYTES_PER_MIB } from '../../app/constants';
import { FILE_ACCEPT, validate_file, type MediaKind, type UploadLimits } from './media';

export function use_upload_limits() {
  return useQuery({
    queryKey: ['upload_limits'],
    queryFn: async ({ signal }): Promise<UploadLimits> => {
      const response = await fetch('/config.json', { signal, cache: 'no-store' });
      if (!response.ok) throw new ApiError(503, 'Не удалось загрузить настройки публикации.');
      const limits: UploadLimits = await response.json();
      if (
        ![limits.image_max_bytes, limits.audio_max_bytes].every(
          (value) => Number.isSafeInteger(value) && value > 0,
        )
      )
        throw new ApiError(503, 'Настройки загрузки недоступны.');
      return limits;
    },
  });
}

export function FileField({
  kind,
  file,
  on_change,
  limits,
  required = false,
}: {
  kind: MediaKind;
  file: File | null;
  on_change: (file: File | null) => void;
  limits: UploadLimits;
  required?: boolean;
}) {
  const input_ref = useRef<HTMLInputElement>(null);
  const [preview_url, set_preview_url] = useState<string | null>(null);
  useEffect(() => {
    if (!file || kind !== 'image') {
      set_preview_url(null);
      return;
    }
    const url = URL.createObjectURL(file);
    set_preview_url(url);
    return () => URL.revokeObjectURL(url);
  }, [file, kind]);
  let error: string | null = null;
  if (file) {
    try {
      validate_file(file, kind, limits);
    } catch (failure) {
      error = (failure as ApiError).message;
    }
  }
  return (
    <div className="file-field">
      <label>
        {kind === 'image' ? 'Обложка' : 'Аудиофайл'}
        {!required && ' · необязательно'}
        <input
          ref={input_ref}
          type="file"
          accept={FILE_ACCEPT[kind]}
          required={required}
          onChange={(event) => on_change(event.target.files?.[0] || null)}
          aria-invalid={!!error}
        />
      </label>
      <small className="muted">
        {kind === 'image' ? 'JPEG, PNG, WebP · статичные изображения' : 'MP3, FLAC, WAV'} · до{' '}
        {Math.floor(
          (kind === 'image' ? limits.image_max_bytes : limits.audio_max_bytes) / BYTES_PER_MIB,
        )}{' '}
        МБ
      </small>
      {file && (
        <div className="file-summary">
          {preview_url && !error && <img src={preview_url} alt="Предпросмотр обложки" />}
          <span>
            {file.name} · {(file.size / BYTES_PER_MIB).toFixed(2)} МБ
          </span>
          <button
            className="text-button"
            type="button"
            onClick={() => {
              on_change(null);
              if (input_ref.current) input_ref.current.value = '';
            }}
          >
            Убрать файл
          </button>
        </div>
      )}
      {error && (
        <p className="field-error" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
