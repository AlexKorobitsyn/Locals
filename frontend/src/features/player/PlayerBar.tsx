import { useState } from 'react';
import { Link } from 'react-router';
import { ListMusic, Pause, Play, SkipBack, SkipForward, Volume2, X } from 'lucide-react';
import { Cover } from '../../components/Cover';
import { format_duration, VOLUME_STEP } from '../../app/constants';
import { use_player } from './PlayerProvider';

export function PlayerBar() {
  const { state, toggle, seek, select, set_volume } = use_player();
  const [show_queue, set_show_queue] = useState(false);
  const track = state.queue[state.current_index];
  return (
    <>
      {show_queue && (
        <aside className="queue-panel" aria-label="Очередь воспроизведения">
          <div className="section-heading">
            <h2>Далее в очереди</h2>
            <button
              className="icon-button"
              aria-label="Закрыть очередь"
              onClick={() => set_show_queue(false)}
            >
              <X />
            </button>
          </div>
          {state.queue.length ? (
            <ol>
              {state.queue.map((item, index) => (
                <li key={`${item.id}:${index}`}>
                  <button
                    className={index === state.current_index ? 'queue-current' : ''}
                    onClick={() => select(index)}
                    aria-current={index === state.current_index ? 'true' : undefined}
                  >
                    {item.title}
                    <span>{format_duration(item.duration)}</span>
                  </button>
                </li>
              ))}
            </ol>
          ) : (
            <p className="muted">Выберите трек в каталоге.</p>
          )}
        </aside>
      )}
      <section className="player-bar" aria-label="Управление воспроизведением">
        <div className="player-track">
          <Cover url={track?.cover_url} name={track?.title || 'Нет трека'} />
          <div>
            {track ? (
              <Link to={`/tracks/${track.id}`}>{track.title}</Link>
            ) : (
              <strong>Музыка начинается с вас</strong>
            )}
            <small className="muted">
              {state.status === 'loading'
                ? 'Загружаем аудио…'
                : track
                  ? 'Locals · сейчас в плеере'
                  : 'Выберите трек и нажмите play'}
            </small>
          </div>
        </div>
        <div className="player-center">
          <div className="player-buttons">
            <button
              className="icon-button"
              aria-label="Предыдущий трек"
              disabled={!track || state.current_index === 0}
              onClick={() => select(state.current_index - 1)}
            >
              <SkipBack size={18} />
            </button>
            <button
              className="player-play"
              aria-label={state.is_playing ? 'Пауза' : 'Воспроизвести'}
              disabled={!track || state.status === 'loading'}
              onClick={toggle}
            >
              {state.is_playing ? <Pause size={20} /> : <Play size={20} />}
            </button>
            <button
              className="icon-button"
              aria-label="Следующий трек"
              disabled={!track || state.current_index + 1 >= state.queue.length}
              onClick={() => select(state.current_index + 1)}
            >
              <SkipForward size={18} />
            </button>
          </div>
          <div className="seek-row">
            <span>{format_duration(state.current_time)}</span>
            <input
              aria-label="Позиция воспроизведения"
              type="range"
              min={0}
              max={state.duration || 1}
              step={1}
              value={Math.min(state.current_time, state.duration || 1)}
              disabled={state.status !== 'ready'}
              onChange={(event) => seek(Number(event.target.value))}
            />
            <span>{format_duration(state.duration)}</span>
          </div>
        </div>
        <div className="player-extra">
          <Volume2 size={18} aria-hidden="true" />
          <input
            aria-label="Громкость"
            type="range"
            min={0}
            max={1}
            step={VOLUME_STEP}
            value={state.volume}
            onChange={(event) => set_volume(Number(event.target.value))}
          />
          <button
            className="icon-button"
            aria-label="Очередь воспроизведения"
            aria-expanded={show_queue}
            onClick={() => set_show_queue(!show_queue)}
          >
            <ListMusic size={20} />
          </button>
        </div>
        {state.error && (
          <div className="player-error" role="alert">
            {state.error}
            <button className="text-button" onClick={toggle}>
              Повторить
            </button>
          </div>
        )}
      </section>
    </>
  );
}
