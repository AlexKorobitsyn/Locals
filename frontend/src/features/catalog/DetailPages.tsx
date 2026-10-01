import { Link, useParams } from 'react-router';
import { useQuery } from '@tanstack/react-query';
import { ListPlus, Play } from 'lucide-react';
import { api, unwrap } from '../../api/client';
import type { RatingTarget } from '../../api/catalog';
import { ApiError } from '../../api/errors';
import { format_duration, parse_id } from '../../app/constants';
import { Cover } from '../../components/Cover';
import { ErrorState, LoadingState } from '../../components/States';
import { use_auth } from '../auth/AuthProvider';
import { use_player } from '../player/PlayerProvider';
import { RatingBadge, RatingControl } from '../ratings/RatingControl';
import { FavoriteButton } from '../library/FavoriteButton';
import { Reviews } from '../reviews/Reviews';
import { CatalogSection } from './CatalogPage';
import { AddToPlaylist } from '../library/AddToPlaylist';
import { FollowButton } from '../social/FollowButton';

function Engagement({
  target_type,
  target_id,
  my_rating,
}: {
  target_type: RatingTarget;
  target_id: number;
  my_rating: number | null;
}) {
  const { user } = use_auth();
  return (
    <>
      <RatingControl
        key={`${user?.id}:${my_rating}`}
        target_type={target_type}
        target_id={target_id}
        my_rating={my_rating}
      />
      <Reviews
        key={`${user?.id}:${target_id}:${target_type}`}
        target_type={target_type}
        target_id={target_id}
        my_rating={my_rating}
      />
    </>
  );
}

export function TrackPage() {
  const track_id = parse_id(useParams().id);
  const { user } = use_auth();
  const player = use_player();
  const query = useQuery({
    queryKey: ['detail', user?.id, 'track', track_id],
    enabled: !!track_id,
    queryFn: async ({ signal }) =>
      unwrap(
        await api.GET('/api/v1/tracks/{track_id}', {
          params: { path: { track_id: track_id! } },
          signal,
        }),
      ),
  });
  if (!track_id) return <ErrorState error={new ApiError(404, 'Такого трека нет.')} />;
  if (query.isPending) return <LoadingState />;
  if (query.isError) return <ErrorState error={query.error} retry={() => void query.refetch()} />;
  const track = query.data;
  return (
    <>
      <Link className="back-link" to="/tracks">
        ← Все треки
      </Link>
      <div className="detail-hero">
        <Cover large url={track.cover_url || track.album?.cover_url} name={track.title} />
        <div>
          <span className="eyebrow">ТРЕК · {format_duration(track.duration)}</span>
          <h1>{track.title}</h1>
          <p className="artist-links">
            {(track.artists || []).map((artist) => (
              <Link key={artist.id} to={`/artists/${artist.id}`}>
                {artist.name}
              </Link>
            ))}
          </p>
          {track.album && (
            <p className="muted">
              Из альбома <Link to={`/albums/${track.album.id}`}>{track.album.title}</Link>
            </p>
          )}
          <RatingBadge
            rating_avg={track.rating_avg}
            ratings_count={track.ratings_count}
            my_rating={track.my_rating}
          />
          <div className="genre-tags">
            {(track.genres || []).map((genre) => (
              <span key={genre.id}>{genre.name}</span>
            ))}
          </div>
          <div className="actions">
            {track.is_owner && (
              <Link className="button" to={`/studio/tracks/${track.id}`}>
                Редактировать
              </Link>
            )}
            <button
              className="button primary"
              disabled={!track.audio_media_id}
              onClick={() => player.play([track])}
            >
              <Play size={18} />
              Слушать
            </button>
            <button
              className="button"
              disabled={!track.audio_media_id}
              onClick={() => player.append(track)}
            >
              <ListPlus size={18} />В очередь
            </button>
            <FavoriteButton
              entity_type="track"
              entity_id={track.id}
              is_liked={track.is_liked_by_me || false}
            />
          </div>
          {!track.audio_media_id && (
            <p className="muted">Аудио пока не загружено. Музыку можно оценить и обсудить.</p>
          )}
          <AddToPlaylist track_id={track.id} />
        </div>
      </div>
      <Engagement target_type="track" target_id={track.id} my_rating={track.my_rating || null} />
      {track.lyrics && (
        <section className="panel">
          <h2>Текст трека</h2>
          <p className="preserve-lines">{track.lyrics}</p>
        </section>
      )}
      {!!track.artist_credits?.length && (
        <section className="panel">
          <h2>Участники записи</h2>
          {track.artist_credits.map((credit) => (
            <p key={`${credit.artist.id}:${credit.role}`}>
              <Link to={`/artists/${credit.artist.id}`}>{credit.artist.name}</Link> ·{' '}
              {credit.role === 'primary' ? 'Основной исполнитель' : credit.role}
            </p>
          ))}
        </section>
      )}
    </>
  );
}

export function AlbumPage() {
  const album_id = parse_id(useParams().id);
  const { user } = use_auth();
  const query = useQuery({
    queryKey: ['detail', user?.id, 'album', album_id],
    enabled: !!album_id,
    queryFn: async ({ signal }) =>
      unwrap(
        await api.GET('/api/v1/albums/{album_id}', {
          params: { path: { album_id: album_id! } },
          signal,
        }),
      ),
  });
  if (!album_id) return <ErrorState error={new ApiError(404, 'Такого альбома нет.')} />;
  if (query.isPending) return <LoadingState />;
  if (query.isError) return <ErrorState error={query.error} retry={() => void query.refetch()} />;
  const album = query.data;
  return (
    <>
      <Link className="back-link" to="/albums">
        ← Все альбомы
      </Link>
      <div className="detail-hero">
        <Cover large url={album.cover_url} name={album.title} />
        <div>
          <span className="eyebrow">
            АЛЬБОМ{album.release_date ? ` · ${new Date(album.release_date).getFullYear()}` : ''}
          </span>
          <h1>{album.title}</h1>
          <p className="artist-links">
            {(album.artists || []).map((artist) => (
              <Link key={artist.id} to={`/artists/${artist.id}`}>
                {artist.name}
              </Link>
            ))}
          </p>
          <p className="muted">
            {album.tracks_count || 0} треков · {format_duration(album.duration || 0)}
          </p>
          <RatingBadge
            rating_avg={album.rating_avg}
            ratings_count={album.ratings_count}
            my_rating={album.my_rating}
          />
          <div className="genre-tags">
            {(album.genres || []).map((genre) => (
              <span key={genre.id}>{genre.name}</span>
            ))}
          </div>
          <FavoriteButton
            entity_type="album"
            entity_id={album.id}
            is_liked={album.is_liked_by_me || false}
          />
          {album.is_owner && (
            <div className="actions">
              <Link className="button" to={`/studio/albums/${album.id}`}>
                Редактировать
              </Link>
              <Link className="button" to={`/studio/tracks/new?album_id=${album.id}`}>
                Загрузить трек
              </Link>
            </div>
          )}
        </div>
      </div>
      <CatalogSection
        key={album.id}
        kind="tracks"
        filters={{ album_id: album.id }}
        title="Треки альбома"
      />
      <Engagement target_type="album" target_id={album.id} my_rating={album.my_rating || null} />
    </>
  );
}

export function ArtistPage() {
  const artist_id = parse_id(useParams().id);
  const { user } = use_auth();
  const query = useQuery({
    queryKey: ['detail', user?.id, 'artist', artist_id],
    enabled: !!artist_id,
    queryFn: async ({ signal }) =>
      unwrap(
        await api.GET('/api/v1/artists/{artist_id}', {
          params: { path: { artist_id: artist_id! } },
          signal,
        }),
      ),
  });
  if (!artist_id) return <ErrorState error={new ApiError(404, 'Такого артиста нет.')} />;
  if (query.isPending) return <LoadingState />;
  if (query.isError) return <ErrorState error={query.error} retry={() => void query.refetch()} />;
  const artist = query.data;
  return (
    <>
      <Link className="back-link" to="/artists">
        ← Все артисты
      </Link>
      <div className="detail-hero artist-hero">
        <Cover large url={artist.image_url} name={artist.name} />
        <div>
          <span className="eyebrow">АРТИСТ{artist.city ? ` · ${artist.city.name}` : ''}</span>
          <h1>{artist.name}</h1>
          <p className="muted">
            {artist.albums_count || 0} альбомов · {artist.tracks_count || 0} треков
          </p>
          <RatingBadge
            rating_avg={artist.rating_avg}
            ratings_count={artist.ratings_count}
            my_rating={artist.my_rating}
          />
          <div className="genre-tags">
            {(artist.genres || []).map((genre) => (
              <span key={genre.id}>{genre.name}</span>
            ))}
          </div>
          <FavoriteButton
            entity_type="artist"
            entity_id={artist.id}
            is_liked={artist.is_liked_by_me || false}
          />
          <div className="actions">
            <FollowButton
              target_type="artist"
              target_id={artist.id}
              followed={artist.is_followed_by_me || false}
            />
            {artist.is_owner && (
              <>
                <Link className="button" to={`/studio/artists/${artist.id}`}>
                  Редактировать
                </Link>
                <Link className="button" to={`/studio/tracks/new?artist_id=${artist.id}`}>
                  Загрузить трек
                </Link>
                <Link className="button" to={`/studio/albums/new?artist_id=${artist.id}`}>
                  Добавить альбом
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
      {artist.bio && (
        <div className="panel">
          <h2>Об артисте</h2>
          <p className="preserve-lines">{artist.bio}</p>
        </div>
      )}
      <CatalogSection
        key={`albums:${artist.id}`}
        kind="albums"
        filters={{ artist_id: artist.id }}
        title="Альбомы"
      />
      <CatalogSection
        key={`tracks:${artist.id}`}
        kind="tracks"
        filters={{ artist_id: artist.id }}
        title="Треки"
      />
      <Engagement target_type="artist" target_id={artist.id} my_rating={artist.my_rating || null} />
    </>
  );
}
