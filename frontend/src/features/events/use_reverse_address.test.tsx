import { afterEach, expect, it, vi } from 'vitest';
import { act, renderHook } from '@testing-library/react';
import { use_reverse_address } from './use_reverse_address';

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});
it('keeps only the latest map selection when responses arrive out of order', async () => {
  vi.useFakeTimers();
  const responses: ((response: Response) => void)[] = [];
  vi.stubGlobal(
    'fetch',
    vi.fn(() => new Promise<Response>((resolve) => responses.push(resolve))),
  );
  const address = vi.fn();
  const { result } = renderHook(() => use_reverse_address(address));
  act(() => result.current.lookup({ lat: 56, lng: 60 }));
  await act(async () => {
    await vi.advanceTimersByTimeAsync(500);
  });
  act(() => result.current.lookup({ lat: 57, lng: 61 }));
  await act(async () => {
    await vi.advanceTimersByTimeAsync(500);
  });
  expect(responses).toHaveLength(2);
  await act(async () => {
    responses[1]!(Response.json({ address: 'Новый адрес' }));
  });
  expect(address).toHaveBeenCalledExactlyOnceWith('Новый адрес');
  await act(async () => {
    responses[0]!(Response.json({ address: 'Старый адрес' }));
  });
  expect(address).toHaveBeenCalledOnce();
  expect(result.current.state).toBe('ready');
});
it('does not replace a manually edited address with a pending response', async () => {
  vi.useFakeTimers();
  let finish!: (response: Response) => void;
  vi.stubGlobal(
    'fetch',
    vi.fn(
      () =>
        new Promise<Response>((resolve) => {
          finish = resolve;
        }),
    ),
  );
  const address = vi.fn();
  const { result } = renderHook(() => use_reverse_address(address));
  act(() => result.current.lookup({ lat: 56, lng: 60 }));
  await act(async () => {
    await vi.advanceTimersByTimeAsync(500);
  });
  act(() => result.current.cancel());
  await act(async () => {
    finish(Response.json({ address: 'Адрес из сети' }));
  });
  expect(address).not.toHaveBeenCalled();
  expect(result.current.state).toBe('idle');
});
