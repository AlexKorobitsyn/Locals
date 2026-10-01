import type { components } from './generated';

type TokenPair = components['schemas']['BrowserToken'];
let tokens: TokenPair | null = null;
let session_version = 0;
const listeners = new Set<() => void>();
const channel =
  typeof window.BroadcastChannel === 'function'
    ? new window.BroadcastChannel('locals-session')
    : null;

function notify_listeners() {
  for (const listener of listeners) listener();
}

export function set_tokens(next_tokens: TokenPair | null, broadcast = false) {
  tokens = next_tokens;
  session_version += 1;
  notify_listeners();
  if (broadcast) channel?.postMessage({ type: 'session', tokens: next_tokens });
}
export function get_tokens() {
  return tokens;
}
export function replace_tokens(next_tokens: TokenPair, broadcast = false) {
  tokens = next_tokens;
  notify_listeners();
  if (broadcast) channel?.postMessage({ type: 'refresh', tokens: next_tokens });
}
export function get_session_version() {
  return session_version;
}

if (channel)
  channel.onmessage = (event: MessageEvent<{ type: string; tokens: TokenPair | null }>) => {
    if (event.data.type === 'session') {
      if (tokens && event.data.tokens?.session_id === tokens.session_id)
        replace_tokens(event.data.tokens);
      else set_tokens(event.data.tokens);
    } else if (
      event.data.type === 'refresh' &&
      event.data.tokens?.session_id === tokens?.session_id
    )
      replace_tokens(event.data.tokens!);
  };
export function subscribe_session(listener: () => void) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}
