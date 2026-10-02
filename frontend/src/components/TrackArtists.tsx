import { Link } from 'react-router';
import type { components } from '../api/generated';

export function TrackArtists({ artists }: { artists: components['schemas']['ArtistShort'][] }) {
  return (
    <span className="track-artists">
      {artists.length
        ? artists.map((artist, index) => (
            <span key={artist.id}>
              {index > 0 && ', '}
              <Link to={`/artists/${artist.id}`}>{artist.name}</Link>
            </span>
          ))
        : 'Артист не указан'}
    </span>
  );
}
