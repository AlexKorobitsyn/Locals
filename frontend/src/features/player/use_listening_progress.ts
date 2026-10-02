import { useEffect, type RefObject } from 'react';
import { api, unwrap } from '../../api/client';
import { query_client } from '../../app/query';

const HEARTBEAT_MS = 10_000;
const AUDIO_READY_FOR_PLAYBACK = 3;
let pending: Promise<void> = Promise.resolve();

export function use_listening_progress(
  audio_ref: RefObject<HTMLAudioElement | null>,
  track_id?: number,
  user_id?: number,
) {
  useEffect(() => {
    const audio = audio_ref.current;
    if (!audio || !track_id || !user_id) return;
    let active = true;
    let listening_id: string | null = null;
    let starting = false;
    let disabled = false;
    function pulse(is_playing: boolean) {
      pending = pending.then(async () => {
        if (!listening_id) return;
        try {
          const result = unwrap(
            await api.PUT('/api/v1/listening/{listening_id}', {
              params: { path: { listening_id } },
              body: { is_playing },
            }),
          );
          if (result.awarded) {
            await query_client.invalidateQueries({ queryKey: ['experience'] });
            await query_client.invalidateQueries({ queryKey: ['me'] });
          }
        } catch {
          disabled = true;
        }
      });
    }
    function start() {
      if (!active || disabled || listening_id || starting) return;
      starting = true;
      pending = pending.then(async () => {
        if (!active) {
          starting = false;
          return;
        }
        try {
          const result = unwrap(
            await api.POST('/api/v1/tracks/{track_id}/listening', {
              params: { path: { track_id: track_id! } },
            }),
          );
          listening_id = result.id;
          if (!active || audio!.paused) pulse(false);
        } catch {
          disabled = true;
        } finally {
          starting = false;
        }
      });
    }
    const pause = () => pulse(false);
    const resume = () => {
      if (listening_id) pulse(true);
      else void start();
    };
    audio.addEventListener('playing', resume);
    audio.addEventListener('pause', pause);
    audio.addEventListener('ended', pause);
    audio.addEventListener('waiting', pause);
    if (!audio.paused) void start();
    const timer = window.setInterval(() => {
      if (!disabled)
        pulse(!audio.paused && !audio.ended && audio.readyState >= AUDIO_READY_FOR_PLAYBACK);
    }, HEARTBEAT_MS);
    return () => {
      active = false;
      window.clearInterval(timer);
      audio.removeEventListener('playing', resume);
      audio.removeEventListener('pause', pause);
      audio.removeEventListener('ended', pause);
      audio.removeEventListener('waiting', pause);
      pulse(false);
    };
  }, [audio_ref, track_id, user_id]);
}
