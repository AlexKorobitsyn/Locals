import type { Track } from '../../api/catalog';
import { DEFAULT_VOLUME } from '../../app/constants';

export type PlayerState = {
  queue: Track[];
  current_index: number;
  is_playing: boolean;
  status: 'idle' | 'loading' | 'ready' | 'error';
  current_time: number;
  duration: number;
  volume: number;
  error: string | null;
};
export type PlayerAction =
  | { type: 'play'; queue: Track[]; index: number }
  | { type: 'select'; index: number }
  | { type: 'append'; track: Track }
  | { type: 'toggle'; is_playing: boolean }
  | { type: 'time'; current_time: number; duration: number }
  | { type: 'volume'; volume: number }
  | { type: 'status'; status: PlayerState['status']; error?: string }
  | { type: 'reset' };

export const initial_state: PlayerState = {
  queue: [],
  current_index: 0,
  is_playing: false,
  status: 'idle',
  current_time: 0,
  duration: 0,
  volume: DEFAULT_VOLUME,
  error: null,
};

export function player_reducer(state: PlayerState, action: PlayerAction): PlayerState {
  switch (action.type) {
    case 'play':
      return action.queue[action.index]
        ? {
            ...state,
            queue: action.queue,
            current_index: action.index,
            is_playing: true,
            status: 'loading',
            current_time: 0,
            duration: action.queue[action.index]!.duration,
            error: null,
          }
        : state;
    case 'select':
      return state.queue[action.index]
        ? {
            ...state,
            current_index: action.index,
            is_playing: true,
            status: 'loading',
            current_time: 0,
            duration: state.queue[action.index]!.duration,
            error: null,
          }
        : state;
    case 'append':
      return { ...state, queue: [...state.queue, action.track] };
    case 'toggle':
      return { ...state, is_playing: action.is_playing };
    case 'time':
      return { ...state, current_time: action.current_time, duration: action.duration };
    case 'volume':
      return { ...state, volume: Math.max(0, Math.min(1, action.volume)) };
    case 'status':
      return {
        ...state,
        status: action.status,
        error: action.error || null,
        ...(action.status === 'error' ? { is_playing: false } : {}),
      };
    case 'reset':
      return { ...initial_state, volume: state.volume };
  }
}
