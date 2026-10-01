import { ApiError, error_message } from '../api/errors';

export function LoadingState() {
  return (
    <div className="state-panel" role="status">
      <span className="spinner" />
      Загружаем музыку…
    </div>
  );
}
export function EmptyState({
  title = 'Пока здесь тихо',
  description = 'Музыка появится здесь, когда её добавят в каталог.',
}: {
  title?: string;
  description?: string;
}) {
  return (
    <div className="state-panel">
      <span className="empty-note" aria-hidden="true">
        ♫
      </span>
      <h3>{title}</h3>
      <p>{description}</p>
    </div>
  );
}
export function ErrorState({ error, retry }: { error: unknown; retry?: () => void }) {
  return (
    <div className="state-panel error-panel" role="alert">
      <h3>
        {error instanceof ApiError && error.status
          ? `Ошибка ${error.status}`
          : 'Не удалось выполнить действие'}
      </h3>
      <p>{error_message(error)}</p>
      {error instanceof ApiError &&
        error.field_errors.map((message) => <p key={message}>{message}</p>)}
      {retry && (
        <button className="button" onClick={retry}>
          Попробовать снова
        </button>
      )}
    </div>
  );
}
