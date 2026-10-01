import { StrictMode } from 'react';
import { createRoot as create_root } from 'react-dom/client';
import { BrowserRouter, Link, Navigate, Route, Routes } from 'react-router';
import { QueryClientProvider } from '@tanstack/react-query';
import { query_client } from './app/query';
import { Layout } from './app/Layout';
import { AuthProvider } from './features/auth/AuthProvider';
import { AuthPage } from './features/auth/AuthPage';
import { PreferencesPage } from './features/auth/PreferencesPage';
import { CatalogPage } from './features/catalog/CatalogPage';
import { AlbumPage, ArtistPage, TrackPage } from './features/catalog/DetailPages';
import { PlayerProvider } from './features/player/PlayerProvider';
import { LibraryPage } from './features/library/LibraryPage';
import { PlaylistPage } from './features/library/PlaylistPage';
import { RecommendationsPage } from './features/recommendations/RecommendationsPage';
import { StudioPage } from './features/studio/StudioPage';
import { CatalogEditorPage } from './features/studio/CatalogEditorPage';
import { ScenePage, EventPage, VenuePage } from './features/events/EventPages';
import { SceneEditorPage } from './features/events/SceneEditorPage';
import { SocialPage } from './features/social/SocialPage';
import { ProfilePage } from './features/social/ProfilePage';
import './styles.css';

function NotFoundPage() {
  return (
    <div className="state-panel">
      <span className="eyebrow">404</span>
      <h1>Здесь пока тишина</h1>
      <p>Такой страницы нет.</p>
      <Link className="button primary" to="/tracks">
        Открыть каталог
      </Link>
    </div>
  );
}

create_root(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={query_client}>
      <AuthProvider>
        <BrowserRouter>
          <PlayerProvider>
            <Routes>
              <Route element={<Layout />}>
                <Route index element={<RecommendationsPage />} />
                <Route path="recommendations" element={<Navigate to="/" replace />} />
                <Route path="tracks" element={<CatalogPage kind="tracks" />} />
                <Route path="tracks/:id" element={<TrackPage />} />
                <Route path="albums" element={<CatalogPage kind="albums" />} />
                <Route path="albums/:id" element={<AlbumPage />} />
                <Route path="artists" element={<CatalogPage kind="artists" />} />
                <Route path="artists/:id" element={<ArtistPage />} />
                <Route path="login" element={<AuthPage key="login" />} />
                <Route path="register" element={<AuthPage key="register" register />} />
                <Route path="preferences" element={<PreferencesPage />} />
                <Route path="library" element={<LibraryPage />} />
                <Route path="playlists/:id" element={<PlaylistPage />} />
                <Route path="studio" element={<StudioPage />} />
                <Route path="studio/artists/new" element={<CatalogEditorPage kind="artists" />} />
                <Route path="studio/artists/:id" element={<CatalogEditorPage kind="artists" />} />
                <Route path="studio/albums/new" element={<CatalogEditorPage kind="albums" />} />
                <Route path="studio/albums/:id" element={<CatalogEditorPage kind="albums" />} />
                <Route path="studio/tracks/new" element={<CatalogEditorPage kind="tracks" />} />
                <Route path="studio/tracks/:id" element={<CatalogEditorPage kind="tracks" />} />
                <Route path="events" element={<ScenePage />} />
                <Route path="events/new" element={<SceneEditorPage />} />
                <Route path="events/:id" element={<EventPage />} />
                <Route path="events/:id/edit" element={<SceneEditorPage />} />
                <Route path="venues" element={<ScenePage venues />} />
                <Route path="venues/new" element={<SceneEditorPage venues />} />
                <Route path="venues/:id" element={<VenuePage />} />
                <Route path="venues/:id/edit" element={<SceneEditorPage venues />} />
                <Route path="feed" element={<SocialPage />} />
                <Route path="following" element={<SocialPage following />} />
                <Route path="users/:id" element={<ProfilePage />} />
                <Route path="*" element={<NotFoundPage />} />
              </Route>
            </Routes>
          </PlayerProvider>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  </StrictMode>,
);
