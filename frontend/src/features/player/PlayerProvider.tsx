import {
  createContext,
  useContext,
  useEffect,
  useReducer,
  useRef,
  useState,
  type ReactNode,
} from 'react';
import type { Track } from '../../api/catalog';
import { api, unwrap } from '../../api/client';
import { error_message } from '../../api/errors';
import { MAX_PLAYBACK_REFRESHES, MS_PER_SECOND } from '../../app/constants';
import { use_auth } from '../auth/AuthProvider';
import { initial_state, player_reducer, type PlayerState } from './reducer';

type PlayerContextValue = {
  state: PlayerState;
  play: (queue: Track[], index?: number) => void;
  append: (track: Track) => void;
  toggle: () => void;
  seek: (time: number) => void;
  set_volume: (volume: number) => void;
  select: (index: number) => void;
  retry: () => void;
};
const PlayerContext = createContext<PlayerContextValue | null>(null);

export function PlayerProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(player_reducer, initial_state);
  const [load_revision, set_load_revision] = useState(0);
  const audio_ref = useRef<HTMLAudioElement>(null);
  const state_ref = useRef(state);
  const expires_at = useRef(0);
  const restore_time = useRef(0);
  const refresh_count = useRef(0);
  const request_generation = useRef(0);
  const { user } = use_auth();
  const previous_user = useRef(user?.id);
  state_ref.current = state;
  const current_track = state.queue[state.current_index];

  useEffect(() => {
    if (previous_user.current !== undefined && previous_user.current !== user?.id)
      dispatch({ type: 'reset' });
    previous_user.current = user?.id;
  }, [user?.id]);

  function fail(message: string) {
    dispatch({ type: 'status', status: 'error', error: message });
  }
  function refresh_source() {
    if (refresh_count.current >= MAX_PLAYBACK_REFRESHES) {
      fail('Не удалось воспроизвести аудио. Повторите попытку.');
      return;
    }
    refresh_count.current += 1;
    restore_time.current = audio_ref.current?.currentTime || state_ref.current.current_time;
    set_load_revision((revision) => revision + 1);
  }
  function request_play(audio: HTMLAudioElement) {
    const generation = request_generation.current;
    void audio.play().catch((error: unknown) => {
      if (generation !== request_generation.current || !state_ref.current.is_playing) return;
      if (error instanceof DOMException && error.name === 'AbortError') return;
      fail('Браузер не начал воспроизведение. Нажмите «Воспроизвести» ещё раз.');
    });
  }

  useEffect(() => {
    const audio = audio_ref.current;
    if (!audio) return;
    const controller = new AbortController();
    const generation = ++request_generation.current;
    audio.pause();
    audio.removeAttribute('src');
    audio.load();
    if (!current_track) return () => controller.abort();
    dispatch({ type: 'status', status: 'loading' });
    void (async () => {
      try {
        const playback = unwrap(
          await api.GET('/api/v1/tracks/{track_id}/playback', {
            params: { path: { track_id: current_track.id } },
            signal: controller.signal,
          }),
        );
        if (controller.signal.aborted || generation !== request_generation.current) return;
        expires_at.current = Date.now() + playback.expires_in * MS_PER_SECOND;
        audio.src = playback.url;
        audio.load();
      } catch (error) {
        if (!controller.signal.aborted) fail(error_message(error));
      }
    })();
    return () => {
      controller.abort();
      ++request_generation.current;
    };
  }, [current_track?.id, state.current_index, load_revision]);

  useEffect(() => {
    const audio = audio_ref.current;
    if (!audio) return;
    audio.volume = state.volume;
    if (!state.is_playing) audio.pause();
    else if (state.status === 'ready') request_play(audio);
  }, [state.is_playing, state.status, state.volume]);

  function select(index: number) {
    if (!state_ref.current.queue[index]) return;
    restore_time.current = 0;
    refresh_count.current = 0;
    dispatch({ type: 'select', index });
    if (index === state_ref.current.current_index) set_load_revision((revision) => revision + 1);
  }
  function play(queue: Track[], index = 0) {
    restore_time.current = 0;
    refresh_count.current = 0;
    dispatch({ type: 'play', queue, index });
    set_load_revision((revision) => revision + 1);
  }
  function toggle() {
    if (state_ref.current.status === 'error') {
      refresh_count.current = 0;
      restore_time.current = state_ref.current.current_time;
      set_load_revision((revision) => revision + 1);
      dispatch({ type: 'toggle', is_playing: true });
    } else {
      if (!state_ref.current.is_playing && Date.now() >= expires_at.current && current_track)
        refresh_source();
      dispatch({ type: 'toggle', is_playing: !state_ref.current.is_playing });
    }
  }
  function seek(time: number) {
    const audio = audio_ref.current;
    if (!audio || !current_track || state_ref.current.status !== 'ready') return;
    if (Date.now() >= expires_at.current) {
      refresh_source();
      restore_time.current = time;
    } else audio.currentTime = time;
    dispatch({ type: 'time', current_time: time, duration: state_ref.current.duration });
  }

  return (
    <PlayerContext.Provider
      value={{
        state,
        play,
        append: (track) => dispatch({ type: 'append', track }),
        toggle,
        seek,
        select,
        set_volume: (volume) => dispatch({ type: 'volume', volume }),
        retry: toggle,
      }}
    >
      {children}
      <audio
        ref={audio_ref}
        preload="metadata"
        aria-label="Аудиоплеер"
        onPlaying={() => {
          refresh_count.current = 0;
        }}
        onLoadedMetadata={() => {
          const audio = audio_ref.current!;
          if (Number.isFinite(audio.duration)) {
            audio.currentTime = Math.min(restore_time.current, audio.duration);
            restore_time.current = 0;
            dispatch({ type: 'time', current_time: audio.currentTime, duration: audio.duration });
          }
          dispatch({ type: 'status', status: 'ready' });
        }}
        onTimeUpdate={() => {
          const audio = audio_ref.current!;
          if (Number.isFinite(audio.duration))
            dispatch({ type: 'time', current_time: audio.currentTime, duration: audio.duration });
        }}
        onEnded={() => {
          if (state_ref.current.current_index + 1 < state_ref.current.queue.length)
            select(state_ref.current.current_index + 1);
          else dispatch({ type: 'toggle', is_playing: false });
        }}
        onError={() => {
          if (!audio_ref.current?.getAttribute('src')) return;
          if (Date.now() >= expires_at.current) refresh_source();
          else fail('Аудиофайл недоступен или его формат не поддерживается браузером.');
        }}
      />
    </PlayerContext.Provider>
  );
}

export function use_player() {
  const context = useContext(PlayerContext);
  if (!context) throw new Error('PlayerProvider is required');
  return context;
}
