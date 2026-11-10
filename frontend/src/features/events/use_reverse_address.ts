import { useEffect, useRef, useState } from 'react';
import { api, unwrap } from '../../api/client';
import { ApiError } from '../../api/errors';
import type { MapPoint } from './map_constants';

const LOOKUP_DELAY_MS = 500;
const RATE_LIMIT_RETRY_MS = 2100;
const MAX_RATE_LIMIT_RETRIES = 2;
type LookupState = 'idle' | 'loading' | 'ready' | 'missing' | 'error';

export function use_reverse_address(on_address: (address: string) => void) {
  const [state, set_state] = useState<LookupState>('idle');
  const controller = useRef<AbortController | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const version = useRef(0);
  const latest_point = useRef<MapPoint | null>(null);
  function abort() {
    version.current += 1;
    controller.current?.abort();
    if (timer.current !== null) clearTimeout(timer.current);
  }
  useEffect(() => () => abort(), []);
  function cancel() {
    abort();
    set_state('idle');
  }
  function lookup(point: MapPoint) {
    abort();
    latest_point.current = point;
    const request_version = version.current;
    set_state('loading');
    async function request(attempt = 0) {
      if (request_version !== version.current) return;
      const current = new AbortController();
      controller.current = current;
      try {
        const data = unwrap(
          await api.GET('/api/v1/geocoding/reverse', {
            params: { query: { lat: point.lat, lng: point.lng } },
            signal: current.signal,
          }),
        );
        if (request_version !== version.current) return;
        if (data.address) on_address(data.address);
        set_state(data.address ? 'ready' : 'missing');
      } catch (error) {
        if (request_version !== version.current || current.signal.aborted) return;
        if (error instanceof ApiError && error.status === 429 && attempt < MAX_RATE_LIMIT_RETRIES) {
          timer.current = setTimeout(() => void request(attempt + 1), RATE_LIMIT_RETRY_MS);
        } else set_state('error');
      }
    }
    timer.current = setTimeout(() => void request(), LOOKUP_DELAY_MS);
  }
  return {
    state,
    lookup,
    cancel,
    retry: () => {
      if (latest_point.current) lookup(latest_point.current);
    },
  };
}
