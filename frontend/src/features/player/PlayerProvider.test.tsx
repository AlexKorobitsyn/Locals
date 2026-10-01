import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { Link, MemoryRouter, Route, Routes } from 'react-router';
import user_event from '@testing-library/user-event';
import { PlayerProvider, use_player } from './PlayerProvider';
import type { Track } from '../../api/catalog';

vi.mock('../auth/AuthProvider', () => ({ use_auth: () => ({ user: null }) }));
const first_track: Track = {
  id: 1,
  title: 'First',
  duration: 120,
  ratings_count: 0,
  likes_count: 0,
  is_liked_by_me: false,
  rating_avg: null,
};
const second_track = { ...first_track, id: 2, title: 'Second' };
beforeEach(() => {
  vi.spyOn(HTMLMediaElement.prototype, 'load').mockImplementation(() => {});
  vi.spyOn(HTMLMediaElement.prototype, 'pause').mockImplementation(() => {});
  vi.spyOn(HTMLMediaElement.prototype, 'play').mockResolvedValue();
});
afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});
function Controls() {
  const player = use_player();
  return (
    <>
      <button onClick={() => player.play([first_track, second_track])}>Start</button>
      <button onClick={() => player.select(1)}>Second</button>
      <button onClick={() => player.seek(60)}>Seek</button>
      <Link to="/album">Album</Link>
      <span data-testid="status">{player.state.status}</span>
    </>
  );
}
function render_player() {
  const view = render(
    <MemoryRouter>
      <PlayerProvider>
        <Controls />
        <Routes>
          <Route path="/" element={<p>Track page</p>} />
          <Route path="/album" element={<p>Album page</p>} />
        </Routes>
      </PlayerProvider>
    </MemoryRouter>,
  );
  return { ...view, audio: view.container.querySelector('audio')! };
}

it('keeps the same audio and source when navigating', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () =>
      Response.json({
        url: 'https://storage.example/first.wav',
        expires_in: 300,
        duration: 120,
        content_type: 'audio/wav',
      }),
    ),
  );
  const { audio, container } = render_player();
  const user = user_event.setup();
  await user.click(screen.getByText('Start'));
  await waitFor(() => expect(audio.src).toBe('https://storage.example/first.wav'));
  Object.defineProperty(audio, 'duration', { value: 120 });
  fireEvent.loadedMetadata(audio);
  audio.currentTime = 45;
  fireEvent.timeUpdate(audio);
  await user.click(screen.getByText('Album'));
  expect(screen.getByText('Album page')).toBeInTheDocument();
  expect(container.querySelector('audio')).toBe(audio);
  expect(audio.currentTime).toBe(45);
  expect(audio.src).toBe('https://storage.example/first.wav');
});

it('renews an expired URL and restores the requested seek position', async () => {
  let now = 1_000_000;
  vi.spyOn(Date, 'now').mockImplementation(() => now);
  const fetch_mock = vi.fn(async () =>
    Response.json({
      url: `https://storage.example/audio-${now}.wav`,
      expires_in: 1,
      duration: 120,
      content_type: 'audio/wav',
    }),
  );
  vi.stubGlobal('fetch', fetch_mock);
  const { audio } = render_player();
  const user = user_event.setup();
  await user.click(screen.getByText('Start'));
  await waitFor(() => expect(audio.src).toBe('https://storage.example/audio-1000000.wav'));
  Object.defineProperty(audio, 'duration', { value: 120 });
  fireEvent.loadedMetadata(audio);
  now += 2_000;
  await user.click(screen.getByText('Seek'));
  await waitFor(() => expect(audio.src).toBe('https://storage.example/audio-1002000.wav'));
  fireEvent.loadedMetadata(audio);
  expect(audio.currentTime).toBe(60);
  expect(fetch_mock).toHaveBeenCalledTimes(2);
  expect(screen.getByTestId('status')).toHaveTextContent('ready');
});

it('stops after one automatic URL renewal when audio keeps failing', async () => {
  let now = 1_000_000;
  vi.spyOn(Date, 'now').mockImplementation(() => now);
  const fetch_mock = vi.fn(async () =>
    Response.json({
      url: `https://storage.example/audio-${now}.wav`,
      expires_in: 1,
      duration: 120,
      content_type: 'audio/wav',
    }),
  );
  vi.stubGlobal('fetch', fetch_mock);
  const { audio } = render_player();
  await user_event.setup().click(screen.getByText('Start'));
  await waitFor(() => expect(audio.src).toContain('audio-1000000'));
  now += 2_000;
  fireEvent.error(audio);
  await waitFor(() => expect(audio.src).toContain('audio-1002000'));
  now += 2_000;
  fireEvent.error(audio);
  expect(screen.getByTestId('status')).toHaveTextContent('error');
  expect(fetch_mock).toHaveBeenCalledTimes(2);
});

it('ignores a slow playback response after a different track is selected', async () => {
  let resolve_first!: (response: Response) => void;
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo | URL) => {
      const url = input instanceof Request ? input.url : String(input);
      if (url.includes('/tracks/1/'))
        return new Promise<Response>((resolve) => {
          resolve_first = resolve;
        });
      return Response.json({
        url: 'https://storage.example/second.wav',
        expires_in: 300,
        duration: 120,
        content_type: 'audio/wav',
      });
    }),
  );
  const { audio } = render_player();
  const user = user_event.setup();
  await user.click(screen.getByText('Start'));
  await waitFor(() => expect(resolve_first).toBeDefined());
  await user.click(screen.getByText('Second'));
  await waitFor(() => expect(audio.src).toBe('https://storage.example/second.wav'));
  resolve_first(
    Response.json({ url: 'https://storage.example/first.wav', expires_in: 300, duration: 120 }),
  );
  await waitFor(() => expect(audio.src).toBe('https://storage.example/second.wav'));
});
