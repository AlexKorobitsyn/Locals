import importlib
import pkgutil
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from pydantic import BaseModel, ValidationError

import APP.schemas
from APP.schemas.album import AlbumRatedShort, AlbumShort
from APP.schemas.artist import ArtistRatedShort, ArtistShort
from APP.schemas.event import EventCreate, EventOut, EventUpdate
from APP.schemas.favorite import FavoriteCreate
from APP.schemas.playlist import PlaylistOut
from APP.schemas.review import ReviewShort
from APP.schemas.track import TrackCreate, TrackRatedShort, TrackShort, TrackUpdate
from APP.schemas.venue import VenueRatedShort, VenueShort

NOW = datetime.now(UTC)


def test_all_schemas_import_and_generate_json_schema():
    for module_info in pkgutil.iter_modules(APP.schemas.__path__):
        module = importlib.import_module(f"APP.schemas.{module_info.name}")
        for value in vars(module).values():
            if (
                isinstance(value, type)
                and value is not BaseModel
                and issubclass(value, BaseModel)
            ):
                value.model_json_schema()


@pytest.mark.parametrize(
    ("short", "rated"),
    [
        (TrackShort, TrackRatedShort),
        (AlbumShort, AlbumRatedShort),
        (ArtistShort, ArtistRatedShort),
        (VenueShort, VenueRatedShort),
    ],
)
def test_short_and_rated_contracts(short, rated):
    assert "rating_avg" not in short.model_fields
    assert {"ratings_count", "my_rating"} <= rated.model_fields.keys()
    assert "rating_avg" in rated.model_computed_fields


def test_nullable_fields_and_orm_serialization():
    track = TrackShort.model_validate(SimpleNamespace(id=1, title="Track", duration=90))
    assert track.cover_url is None
    event = EventOut(
        id=1,
        name="Jam",
        starts_at=NOW,
        venue={
            "id": 1,
            "name": "Club",
            "city": {"id": 1, "name": "City"},
            "lat": 56,
            "lng": 60,
        },
        stop_at=None,
    )
    assert event.model_dump(mode="json")["stop_at"] is None


def test_playlist_details_do_not_embed_tracks():
    playlist = PlaylistOut(
        id=1,
        name="Liked",
        owner={"id": 1, "display_name": "Listener"},
        visibility="private",
        created_at=NOW,
        updated_at=NOW,
    )
    assert "tracks" not in playlist.model_dump()
    assert "tracks" not in PlaylistOut.model_json_schema()["properties"]


@pytest.mark.parametrize(
    "changes",
    [
        {"title": "  "},
        {"duration": 0},
        {"duration": -1},
        {"album_id": 0},
        {"artist_ids": [-1]},
        {"artist_ids": [True]},
        {"user_id": 1},
    ],
)
def test_track_create_rejects_invalid_input(changes):
    payload = {"title": "Track", "duration": 90} | changes
    with pytest.raises(ValidationError):
        TrackCreate.model_validate(payload)


def test_track_create_trims_title_and_has_independent_lists():
    first = TrackCreate(title="  Track  ", duration=90)
    second = TrackCreate(title="Other", duration=90)
    first.artist_ids.append(1)
    assert first.title == "Track"
    assert second.artist_ids == []


def test_patch_distinguishes_omitted_fields_from_explicit_null():
    assert TrackUpdate().model_dump(exclude_unset=True) == {}
    assert TrackUpdate(album_id=None).model_dump(exclude_unset=True) == {
        "album_id": None
    }
    assert EventUpdate(stop_at=None).model_dump(exclude_unset=True) == {"stop_at": None}


@pytest.mark.parametrize(
    ("schema", "payload"),
    [
        (TrackUpdate, {"title": None}),
        (TrackUpdate, {"artist_ids": None}),
        (EventUpdate, {"name": None}),
        (EventUpdate, {"starts_at": None}),
        (EventUpdate, {"type_event_ids": None}),
    ],
)
def test_patch_rejects_null_for_non_nullable_fields(schema, payload):
    with pytest.raises(ValidationError):
        schema.model_validate(payload)


@pytest.mark.parametrize("schema", [EventCreate, EventUpdate])
def test_events_reject_end_before_start(schema):
    with pytest.raises(ValidationError):
        schema(
            name="Jam",
            venue_id=1,
            starts_at=NOW,
            stop_at=NOW - timedelta(hours=1),
        )


def test_events_require_timezone():
    with pytest.raises(ValidationError):
        EventCreate(name="Jam", venue_id=1, starts_at=NOW.replace(tzinfo=None))


@pytest.mark.parametrize("rating", [0, 6, float("nan"), float("inf")])
def test_review_rating_range(rating):
    with pytest.raises(ValidationError):
        ReviewShort(id=1, rating=rating, created_at=NOW)


def test_favorites_validate_entity_and_id():
    favorite = FavoriteCreate(entity_type="track", entity_id=1)
    assert favorite.model_dump(mode="json")["entity_type"] == "track"
    with pytest.raises(ValidationError):
        FavoriteCreate(entity_type="user", entity_id=1)
    with pytest.raises(ValidationError):
        FavoriteCreate(entity_type="track", entity_id=0)
