from enum import StrEnum

NAME_MAX_LENGTH = 255
EMAIL_MAX_LENGTH = 320
ROLE_MAX_LENGTH = 64
SLUG_MAX_LENGTH = 100
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128
JWT_SECRET_MIN_LENGTH = 32
MIN_BCRYPT_ROUNDS = 4
MAX_BCRYPT_ROUNDS = 31
REFRESH_TOKEN_BYTES = 48
TOKEN_HASH_LENGTH = 64
DEFAULT_ARTIST_ROLE = "primary"
DEFAULT_MEMBER_ROLE = "member"
DEFAULT_PAGE_LIMIT = 20
MAX_PAGE_LIMIT = 100
MAX_RELATIONS = 100
BIO_MAX_LENGTH = 10_000
LYRICS_MAX_LENGTH = 100_000
MAX_DATABASE_INTEGER = 2_147_483_647
MIN_RATING = 1
MAX_RATING = 5
RATING_STEP = "0.5"
DEFAULT_RATING_PRIOR_STRENGTH = "50"
DEFAULT_RATING_PRIOR_MEAN = "3"
DEFAULT_RATING_WEIGHT_GREEN = "1"
DEFAULT_RATING_WEIGHT_PRIVILEGED = "2"
REVIEW_MAX_LENGTH = 50_000
DESCRIPTION_MAX_LENGTH = 10_000
PLAYLIST_MAX_TRACKS = 10_000
UPLOAD_CHUNK_BYTES = 1024 * 1024
SHA256_LENGTH = 64


class PlaylistKind(StrEnum):
    custom = "custom"
    liked = "liked"


class FavoriteTarget(StrEnum):
    track = "track"
    album = "album"
    artist = "artist"
    playlist = "playlist"
    event = "event"
    venue = "venue"
    review = "review"


class FollowTarget(StrEnum):
    user = "user"
    artist = "artist"
    venue = "venue"


class UserLevel(StrEnum):
    green = "green"
    experienced = "experienced"
    moderator = "moderator"
    admin = "admin"


class RatingTarget(StrEnum):
    track = "track"
    album = "album"
    artist = "artist"
    venue = "venue"


PRIVILEGED_LEVELS = frozenset(
    {UserLevel.experienced, UserLevel.moderator, UserLevel.admin}
)

DEFAULT_EVENT_TYPE_ID = 1

RECOMMENDATION_NEUTRAL_RATING = 3
DEFAULT_RECOMMENDATION_FAVORITE_WEIGHT = "2"
DEFAULT_RECOMMENDATION_RATED_WEIGHT = "1"
DEFAULT_RECOMMENDATION_QUALITY_WEIGHT = "1"
