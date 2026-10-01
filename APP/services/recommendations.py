from decimal import Decimal

from sqlalchemy import (
    Integer,
    Numeric,
    case,
    column,
    exists,
    false,
    func,
    literal,
    select,
    true,
    union,
    union_all,
    values,
)
from sqlalchemy.orm import selectinload

from APP.core.constants import MAX_RATING, MIN_RATING, RECOMMENDATION_NEUTRAL_RATING
from APP.models.artist import Artist
from APP.models.favorite import Favorite
from APP.models.genre import Genre, album_genres, artist_genres, track_genres
from APP.models.media import Media
from APP.models.rating import Rating
from APP.models.track import Track
from APP.models.track_artist import TrackArtist
from APP.schemas.artist import ArtistShort
from APP.schemas.genre import GenreOut
from APP.schemas.recommendation import (
    GenrePreference,
    RecommendationPage,
    RecommendationScore,
    RecommendedTrack,
)
from APP.services.engagement import set_engagement, with_engagement
from APP.services.preferences import favorite_genres
from APP.services.ratings import (
    rating_average_expression,
    set_rating_context,
    with_my_rating,
)


def effective_track_genres():
    own = exists(
        select(track_genres.c.genre_id)
        .where(track_genres.c.track_id == Track.id)
        .correlate(Track)
    )
    album = exists(
        select(album_genres.c.genre_id)
        .where(album_genres.c.album_id == Track.album_id)
        .correlate(Track)
    )
    # Жанры трека имеют приоритет; роли одного артиста не дублируют жанр.
    return union(
        select(track_genres.c.track_id, track_genres.c.genre_id),
        select(Track.id.label("track_id"), album_genres.c.genre_id)
        .join(album_genres, album_genres.c.album_id == Track.album_id)
        .where(~own),
        select(Track.id.label("track_id"), artist_genres.c.genre_id)
        .join(TrackArtist, TrackArtist.track_id == Track.id)
        .join(artist_genres, artist_genres.c.artist_id == TrackArtist.artist_id)
        .where(~own, ~album),
    ).cte("effective_genres")


async def genre_preferences(session, user, effective):
    if user is None:
        return {}
    ratings = union_all(
        select(effective.c.genre_id, Rating.value)
        .join(Rating, Rating.track_id == effective.c.track_id)
        .where(Rating.user_id == user.id),
        select(album_genres.c.genre_id, Rating.value)
        .join(Rating, Rating.album_id == album_genres.c.album_id)
        .where(Rating.user_id == user.id),
        select(artist_genres.c.genre_id, Rating.value)
        .join(Rating, Rating.artist_id == artist_genres.c.artist_id)
        .where(Rating.user_id == user.id),
    ).cte("personal_genre_ratings")
    rows = (
        await session.execute(
            select(
                Genre,
                func.avg(ratings.c.value - RECOMMENDATION_NEUTRAL_RATING).label(
                    "affinity"
                ),
                func.count().label("ratings_count"),
            )
            .join(ratings, ratings.c.genre_id == Genre.id)
            .group_by(Genre.id)
        )
    ).all()
    return {
        row.Genre.id: GenrePreference(
            genre=GenreOut.model_validate(row.Genre),
            affinity=float(row.affinity),
            ratings_count=row.ratings_count,
        )
        for row in rows
    }


def playable_expression():
    return exists(
        select(Media.id)
        .where(
            Media.id == Track.audio_media_id,
            Media.status == "ready",
            Media.kind == "audio",
        )
        .correlate(Track)
    )


def candidate_filters(user, playable_only):
    filters = [playable_expression()] if playable_only else []
    if user is not None:
        filters.extend(
            [
                ~exists(
                    select(Rating.id)
                    .where(Rating.user_id == user.id, Rating.track_id == Track.id)
                    .correlate(Track)
                ),
                ~exists(
                    select(Favorite.id)
                    .where(Favorite.user_id == user.id, Favorite.track_id == Track.id)
                    .correlate(Track)
                ),
                (Track.user_id.is_(None) | (Track.user_id != user.id)),
                ~exists(
                    select(TrackArtist.track_id)
                    .join(Artist, Artist.id == TrackArtist.artist_id)
                    .where(TrackArtist.track_id == Track.id, Artist.user_id == user.id)
                    .correlate(Track)
                ),
            ]
        )
    return filters


async def recommend_tracks(session, user, settings, limit, offset, playable_only=False):
    effective = effective_track_genres()
    favorites = await favorite_genres(session, user) if user is not None else []
    preferences = await genre_preferences(session, user, effective)
    favorite_ids = {genre.id for genre in favorites}
    personalized = bool(
        favorite_ids or any(item.affinity != 0 for item in preferences.values())
    )
    # Фиксируем личные сигналы для ранжирования и объяснения одной выдачи.
    affinity_rows = [
        (key, Decimal(str(item.affinity))) for key, item in preferences.items()
    ]
    affinities = (
        values(column("genre_id", Integer), column("affinity", Numeric))
        .data(affinity_rows)
        .cte("genre_affinities")
        if affinity_rows
        else select(
            literal(None, Integer).label("genre_id"),
            literal(0, Numeric).label("affinity"),
        )
        .where(false())
        .cte("genre_affinities")
    )
    genre_count = func.count(effective.c.genre_id)
    favorite_component = settings.recommendation_favorite_weight * case(
        (genre_count == 0, 0),
        else_=func.sum(case((effective.c.genre_id.in_(favorite_ids), 1), else_=0)).cast(
            Numeric
        )
        / genre_count,
    )
    rated_component = settings.recommendation_rated_weight * func.coalesce(
        func.avg(func.coalesce(affinities.c.affinity, 0)), 0
    )
    average = rating_average_expression(Track, settings)
    quality_component = (
        settings.recommendation_quality_weight
        * (func.coalesce(average, settings.rating_prior_mean) - MIN_RATING)
        / (MAX_RATING - MIN_RATING)
    )
    scored = (
        select(
            Track.id.label("track_id"),
            Track.ratings_count,
            favorite_component.label("favorite_genre_score"),
            rated_component.label("rated_genre_score"),
            quality_component.label("quality_score"),
            (favorite_component + rated_component + quality_component).label(
                "score_total"
            ),
            func.array_agg(effective.c.genre_id)
            .filter(effective.c.genre_id.is_not(None))
            .label("genre_ids"),
        )
        .outerjoin(effective, effective.c.track_id == Track.id)
        .outerjoin(affinities, affinities.c.genre_id == effective.c.genre_id)
        .where(*candidate_filters(user, playable_only))
        .group_by(Track.id)
        .cte("scored_tracks")
    )
    ordering = [
        scored.c.score_total.desc(),
        scored.c.ratings_count.desc(),
        scored.c.track_id.asc(),
    ]
    page = (
        select(scored)
        .order_by(*ordering)
        .limit(limit)
        .offset(offset)
        .cte("recommendation_page")
    )
    total = select(func.count().label("total")).select_from(scored).subquery()
    query = (
        select(
            Track,
            total.c.total,
            page.c.favorite_genre_score,
            page.c.rated_genre_score,
            page.c.quality_score,
            page.c.score_total,
            page.c.genre_ids,
            playable_expression().label("is_playable"),
        )
        .select_from(
            total.outerjoin(page, true()).outerjoin(Track, Track.id == page.c.track_id)
        )
        .options(selectinload(Track.artists))
        .order_by(
            page.c.score_total.desc(), page.c.ratings_count.desc(), Track.id.asc()
        )
    )
    rows = (
        await session.execute(
            with_engagement(
                with_my_rating(query, Track, "track", user), Track, "track", user
            )
        )
    ).all()
    ids = {genre_id for row in rows for genre_id in row.genre_ids or []}
    genres = (
        {
            genre.id: GenreOut.model_validate(genre)
            for genre in (
                await session.scalars(select(Genre).where(Genre.id.in_(ids)))
            ).all()
        }
        if ids
        else {}
    )
    items = []
    for row in rows:
        if row.Track is None:
            continue
        track_genre_ids = sorted(
            row.genre_ids or [],
            key=lambda key: (genres[key].name if key in genres else "", key),
        )
        track_preferences = [
            preferences[key] for key in track_genre_ids if key in preferences
        ]
        reasons = []
        if row.favorite_genre_score > 0:
            reasons.append("favorite_genres")
        if row.rated_genre_score > 0:
            reasons.append("high_rated_genres")
        elif row.rated_genre_score < 0:
            reasons.append("low_rated_genres")
        if row.Track.ratings_count:
            reasons.append("community_rating")
        if not reasons:
            reasons.append("catalog_fallback")
        output = RecommendedTrack(
            **{
                key: getattr(row.Track, key)
                for key in (
                    "id",
                    "title",
                    "duration",
                    "cover_url",
                    "rating_sum",
                    "rating_weight",
                    "ratings_count",
                )
            },
            artists=[
                ArtistShort.model_validate(artist) for artist in row.Track.artists
            ],
            genres=[genres[key] for key in track_genre_ids if key in genres],
            matched_favorite_genres=[
                genres[key]
                for key in track_genre_ids
                if key in favorite_ids and key in genres
            ],
            genre_preferences=track_preferences,
            score=RecommendationScore(
                favorite_genre_score=float(row.favorite_genre_score),
                rated_genre_score=float(row.rated_genre_score),
                quality_score=float(row.quality_score),
                total=float(row.score_total),
            ),
            reasons=reasons,
            is_playable=row.is_playable,
        )
        items.append(
            set_engagement(set_rating_context(output, row.my_rating, settings), row)
        )
    return RecommendationPage(
        items=items,
        total=rows[0].total,
        limit=limit,
        offset=offset,
        mode="personalized" if personalized else "popular",
    )
