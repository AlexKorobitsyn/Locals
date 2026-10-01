import { useEffect, useRef, useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { api, unwrap } from '../../api/client';
import { ApiError } from '../../api/errors';
import { PERCENT_TOTAL } from '../../app/constants';
import { invalidate_music } from '../../app/query';
import { ErrorState, LoadingState } from '../../components/States';
import { FileField, use_upload_limits } from './FileField';
import { upload_file } from './media';

export function ImageUpload({
  target_type,
  target_id,
}: {
  target_type: 'user' | 'venue' | 'playlist';
  target_id: number;
}) {
  const limits = use_upload_limits();
  const [file, set_file] = useState<File | null>(null);
  const [progress, set_progress] = useState(0);
  const controller = useRef<AbortController | null>(null);
  const uploaded = useRef<{ file: File; id: number } | null>(null);
  useEffect(() => () => controller.current?.abort(), []);
  const mutation = useMutation({
    mutationFn: async () => {
      if (!file || !limits.data) return;
      const current = new AbortController();
      controller.current = current;
      if (uploaded.current?.file !== file) {
        const media = await upload_file(file, 'image', limits.data, set_progress, current.signal);
        uploaded.current = { file, id: media.id };
      }
      unwrap(
        await api.PUT('/api/v1/images/{target_type}/{target_id}', {
          params: { path: { target_type, target_id } },
          body: { media_id: uploaded.current.id },
          signal: current.signal,
        }),
      );
    },
    onSuccess: async () => {
      set_file(null);
      await invalidate_music();
    },
  });
  if (limits.isPending) return <LoadingState />;
  if (limits.isError)
    return <ErrorState error={limits.error} retry={() => void limits.refetch()} />;
  return (
    <form
      className="panel form"
      onSubmit={(event) => {
        event.preventDefault();
        mutation.mutate();
      }}
    >
      <h2>{target_type === 'user' ? 'Фото профиля' : 'Обложка'}</h2>
      <fieldset className="form-fields" disabled={mutation.isPending}>
        <FileField
          key={mutation.isSuccess && !file ? 'empty' : 'file'}
          kind="image"
          file={file}
          on_change={(next) => {
            mutation.reset();
            set_file(next);
          }}
          limits={limits.data}
        />
      </fieldset>
      <button className="button" disabled={!file || mutation.isPending}>
        Сохранить изображение
      </button>
      {mutation.isPending && (
        <div role="status">
          <span>
            {progress < PERCENT_TOTAL
              ? `Загружаем · ${progress}%`
              : 'Проверяем и сохраняем изображение…'}
          </span>
          <progress value={progress} max={PERCENT_TOTAL} aria-label="Прогресс загрузки" />
          <button type="button" className="text-button" onClick={() => controller.current?.abort()}>
            Отменить
          </button>
        </div>
      )}
      {mutation.isError && (
        <ErrorState
          error={
            mutation.error instanceof DOMException && mutation.error.name === 'AbortError'
              ? new ApiError(0, 'Загрузка отменена.')
              : mutation.error
          }
        />
      )}
      {mutation.isSuccess && !file && (
        <p className="success-message" role="status">
          Изображение сохранено.
        </p>
      )}
    </form>
  );
}
