import { Component, useEffect, useState, useSyncExternalStore, type ReactNode } from 'react';
import { Link, NavLink, Outlet, useLocation } from 'react-router';
import {
  Album,
  AudioLines,
  Disc3,
  Headphones,
  Library,
  LogOut,
  Menu,
  SlidersHorizontal,
  Sparkles,
  Users,
  X,
  CalendarDays,
  MapPin,
  Radio,
  Upload,
} from 'lucide-react';
import { error_message } from '../api/errors';
import { use_auth } from '../features/auth/AuthProvider';
import { PlayerBar } from '../features/player/PlayerBar';
import { ErrorState } from '../components/States';

const NAV_ITEMS = [
  { to: '/', label: 'Моя волна', icon: Sparkles },
  { to: '/tracks', label: 'Треки', icon: AudioLines },
  { to: '/albums', label: 'Альбомы', icon: Album },
  { to: '/artists', label: 'Артисты', icon: Users },
  { to: '/library', label: 'Библиотека', icon: Library },
  { to: '/preferences', label: 'Мой вкус', icon: SlidersHorizontal },
  { to: '/events', label: 'События', icon: CalendarDays },
  { to: '/venues', label: 'Площадки', icon: MapPin },
  { to: '/feed', label: 'Лента', icon: Radio },
  { to: '/studio', label: 'Студия', icon: Upload },
];
const mobile_query = window.matchMedia('(max-width: 850px)');
function subscribe_mobile(listener: () => void) {
  mobile_query.addEventListener('change', listener);
  return () => mobile_query.removeEventListener('change', listener);
}

class PageBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  render() {
    return this.state.failed ? (
      <ErrorState error={new Error('page')} retry={() => this.setState({ failed: false })} />
    ) : (
      this.props.children
    );
  }
}

export function Layout() {
  const { user, logout, is_loading, error: auth_error } = use_auth();
  const location = useLocation();
  const [menu_open, set_menu_open] = useState(false);
  const is_mobile = useSyncExternalStore(subscribe_mobile, () => mobile_query.matches);
  const [logout_pending, set_logout_pending] = useState(false);
  const [logout_error, set_logout_error] = useState<string | null>(null);
  useEffect(() => {
    set_menu_open(false);
    window.scrollTo({ top: 0 });
  }, [location.pathname]);
  useEffect(() => {
    if (!menu_open) return;
    function close_on_escape(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        set_menu_open(false);
        document.getElementById('mobile-menu-button')?.focus();
      }
    }
    window.addEventListener('keydown', close_on_escape);
    return () => window.removeEventListener('keydown', close_on_escape);
  }, [menu_open]);
  async function handle_logout() {
    set_logout_pending(true);
    set_logout_error(null);
    try {
      await logout();
    } catch (error) {
      set_logout_error(error_message(error));
    } finally {
      set_logout_pending(false);
    }
  }
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">
        К содержимому
      </a>
      <aside
        id="sidebar"
        className={`sidebar ${menu_open ? 'sidebar-open' : ''}`}
        inert={is_mobile && !menu_open}
      >
        <Link to="/" className="wordmark">
          <Disc3 size={30} />
          locals<span>®</span>
        </Link>
        <p className="sidebar-caption">ВНЕ ОСНОВНОЙ ЧАСТОТЫ</p>
        <nav aria-label="Основная навигация">
          {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to} end={to === '/'}>
              <Icon size={19} />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          <Headphones size={25} />
          <strong>Своя сцена. Свои правила.</strong>
          <p>
            Слушайте, выпускайте,
            <br />
            находите своих.
          </p>
          <span className="sidebar-small">СДЕЛАНО ДЛЯ ТЕХ, КТО СЛУШАЕТ</span>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div className="topbar-start">
            <button
              id="mobile-menu-button"
              className="icon-button mobile-menu"
              aria-controls="sidebar"
              aria-label={menu_open ? 'Закрыть меню' : 'Открыть меню'}
              aria-expanded={menu_open}
              onClick={() => set_menu_open(!menu_open)}
            >
              {menu_open ? <X /> : <Menu />}
            </button>
            <span className="topbar-label">НЕЗАВИСИМАЯ МУЗЫКА. ЛИЧНЫЙ ВКУС.</span>
          </div>
          <div className="account-actions">
            {is_loading ? (
              <span className="muted" role="status">
                Вход…
              </span>
            ) : user ? (
              <>
                <Link to={`/users/${user.id}`} className="account-name">
                  <span className="avatar-letter" aria-hidden="true">
                    {user.display_name.slice(0, 1).toUpperCase()}
                  </span>
                  <span>{user.display_name}</span>
                </Link>
                <button
                  className="icon-button"
                  aria-label="Выйти"
                  disabled={logout_pending}
                  onClick={() => void handle_logout()}
                >
                  <LogOut size={18} />
                </button>
              </>
            ) : (
              <>
                <Link className="text-button" to="/login">
                  Войти
                </Link>
                <Link className="button small primary" to="/register">
                  Присоединиться
                </Link>
              </>
            )}
          </div>
        </header>
        {logout_error && (
          <p className="banner-error" role="alert">
            {logout_error}
          </p>
        )}
        {!!auth_error && (
          <div className="banner-error" role="alert">
            {error_message(auth_error)} <Link to="/login">Войти снова</Link>
          </div>
        )}
        <main id="main-content" tabIndex={-1}>
          <PageBoundary key={location.pathname}>
            <Outlet />
          </PageBoundary>
        </main>
        <footer className="page-footer">
          <span>LOCALS · МУЗЫКА РЯДОМ</span>
          <span>Открывайте с любопытством. Оценивайте со смыслом.</span>
        </footer>
      </div>
      <PlayerBar />
    </div>
  );
}
