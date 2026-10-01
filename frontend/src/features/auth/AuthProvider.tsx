import {
  createContext,
  useContext,
  useEffect,
  useState,
  useSyncExternalStore,
  type ReactNode,
} from 'react';
import { useQuery } from '@tanstack/react-query';
import type { components } from '../../api/generated';
import { api, logout_browser, restore_session, unwrap } from '../../api/client';
import { get_tokens, subscribe_session } from '../../api/session';
import { query_client } from '../../app/query';

type AuthContextValue = {
  user: components['schemas']['UserMe'] | null;
  is_loading: boolean;
  error: unknown;
  logout: () => Promise<void>;
};
const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const tokens = useSyncExternalStore(subscribe_session, get_tokens);
  const [restoring, set_restoring] = useState(true);
  const [restore_error, set_restore_error] = useState<unknown>(null);
  useEffect(() => {
    let active = true;
    void restore_session()
      .catch((error: unknown) => {
        if (active) set_restore_error(error);
      })
      .finally(() => {
        if (active) set_restoring(false);
      });
    return () => {
      active = false;
    };
  }, []);
  const me_query = useQuery({
    queryKey: ['me', tokens?.session_id],
    enabled: !!tokens,
    retry: false,
    queryFn: async ({ signal }) => unwrap(await api.GET('/api/v1/me', { signal })),
  });
  useEffect(() => {
    let previous_session = get_tokens()?.session_id;
    return subscribe_session(() => {
      const current_session = get_tokens()?.session_id;
      if (current_session !== previous_session) query_client.clear();
      previous_session = current_session;
    });
  }, []);

  async function logout() {
    await logout_browser();
  }

  return (
    <AuthContext.Provider
      value={{
        user: tokens ? me_query.data || null : null,
        is_loading: restoring || (!!tokens && me_query.isPending),
        error: tokens ? me_query.error : restore_error,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function use_auth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('AuthProvider is required');
  return context;
}
