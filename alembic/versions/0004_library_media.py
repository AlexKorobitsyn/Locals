"""Рецензии, библиотека, медиа, события и подписки

Revision ID: 0004_library_media
Revises: 0003_ratings
"""

import sqlalchemy as sa

from alembic import op

revision = "0004_library_media"
down_revision = "0003_ratings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "event_types",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_event_types")),
        sa.UniqueConstraint("slug", name=op.f("uq_event_types_slug")),
    )
    op.create_table(
        "media",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "status", sa.String(length=64), server_default="pending", nullable=False
        ),
        sa.Column("kind", sa.String(length=64), nullable=False),
        sa.Column("object_key", sa.Text(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=255), nullable=False),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("duration", sa.Numeric(precision=20, scale=6), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "(kind = 'audio' AND duration IS NOT NULL AND duration > 0 AND width IS NULL AND height IS NULL) OR (kind = 'image' AND width IS NOT NULL AND height IS NOT NULL AND width > 0 AND height > 0 AND duration IS NULL)",
            name=op.f("ck_media_metadata_valid"),
        ),
        sa.CheckConstraint(
            "kind IN ('audio','image')", name=op.f("ck_media_kind_valid")
        ),
        sa.CheckConstraint(
            "status IN ('pending','ready')", name=op.f("ck_media_status_valid")
        ),
        sa.CheckConstraint("size > 0", name=op.f("ck_media_size_positive")),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_media_user_id_users"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_media")),
        sa.UniqueConstraint("object_key", name=op.f("uq_media_object_key")),
    )
    op.create_index(op.f("ix_media_user_id"), "media", ["user_id"], unique=False)
    op.create_table(
        "playlists",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("cover_url", sa.Text(), nullable=True),
        sa.Column("image_media_id", sa.Integer(), nullable=True),
        sa.Column(
            "visibility",
            sa.Enum(
                "public",
                "private",
                name="playlist_visibility",
                native_enum=False,
                create_constraint=True,
            ),
            server_default="private",
            nullable=False,
        ),
        sa.Column(
            "kind",
            sa.Enum(
                "custom",
                "liked",
                name="playlist_kind",
                native_enum=False,
                create_constraint=True,
            ),
            server_default="custom",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "kind <> 'liked' OR visibility = 'private'",
            name=op.f("ck_playlists_liked_private"),
        ),
        sa.CheckConstraint(
            "length(btrim(name)) > 0", name=op.f("ck_playlists_name_nonempty")
        ),
        sa.ForeignKeyConstraint(
            ["image_media_id"],
            ["media.id"],
            name=op.f("fk_playlists_image_media_id_media"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_playlists_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_playlists")),
    )
    op.create_index(
        op.f("ix_playlists_image_media_id"),
        "playlists",
        ["image_media_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_playlists_user_id"), "playlists", ["user_id"], unique=False
    )
    op.create_index(
        "uq_playlists_liked_user",
        "playlists",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("kind = 'liked'"),
    )
    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("city_id", sa.Integer(), nullable=False),
        sa.Column("venue_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("stop_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lng", sa.Float(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "lat BETWEEN -90 AND 90", name=op.f("ck_events_latitude_valid")
        ),
        sa.CheckConstraint(
            "length(btrim(name)) > 0", name=op.f("ck_events_name_nonempty")
        ),
        sa.CheckConstraint(
            "lng BETWEEN -180 AND 180", name=op.f("ck_events_longitude_valid")
        ),
        sa.CheckConstraint(
            "stop_at IS NULL OR stop_at > starts_at", name=op.f("ck_events_dates_valid")
        ),
        sa.ForeignKeyConstraint(
            ["city_id"],
            ["cities.id"],
            name=op.f("fk_events_city_id_cities"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_events_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["venue_id"],
            ["venues.id"],
            name=op.f("fk_events_venue_id_venues"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_events")),
    )
    op.create_index(
        "ix_events_city_starts_at", "events", ["city_id", "starts_at"], unique=False
    )
    op.create_index("ix_events_coordinates", "events", ["lat", "lng"], unique=False)
    op.create_index(op.f("ix_events_user_id"), "events", ["user_id"], unique=False)
    op.create_index(op.f("ix_events_venue_id"), "events", ["venue_id"], unique=False)
    op.create_table(
        "follows",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("follower_id", sa.Integer(), nullable=False),
        sa.Column(
            "target_type",
            sa.Enum(
                "user",
                "artist",
                "venue",
                name="follow_target",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("target_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("artist_id", sa.Integer(), nullable=True),
        sa.Column("venue_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "num_nonnulls(user_id, artist_id, venue_id) = 1 AND ((target_type = 'user' AND user_id IS NOT NULL AND target_id = user_id) OR (target_type = 'artist' AND artist_id IS NOT NULL AND target_id = artist_id) OR (target_type = 'venue' AND venue_id IS NOT NULL AND target_id = venue_id))",
            name=op.f("ck_follows_target_consistent"),
        ),
        sa.CheckConstraint(
            "target_type <> 'user' OR follower_id <> target_id",
            name=op.f("ck_follows_no_self_follow"),
        ),
        sa.CheckConstraint("target_id > 0", name=op.f("ck_follows_target_id_positive")),
        sa.ForeignKeyConstraint(
            ["artist_id"],
            ["artists.id"],
            name=op.f("fk_follows_artist_id_artists"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["follower_id"],
            ["users.id"],
            name=op.f("fk_follows_follower_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_follows_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["venue_id"],
            ["venues.id"],
            name=op.f("fk_follows_venue_id_venues"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_follows")),
        sa.UniqueConstraint(
            "follower_id",
            "target_type",
            "target_id",
            name=op.f("uq_follows_follower_id"),
        ),
    )
    op.create_index(
        op.f("ix_follows_artist_id"), "follows", ["artist_id"], unique=False
    )
    op.create_index(
        "ix_follows_target", "follows", ["target_type", "target_id"], unique=False
    )
    op.create_index(op.f("ix_follows_user_id"), "follows", ["user_id"], unique=False)
    op.create_index(op.f("ix_follows_venue_id"), "follows", ["venue_id"], unique=False)
    op.create_table(
        "event_event_types",
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("event_type_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["events.id"],
            name=op.f("fk_event_event_types_event_id_events"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["event_type_id"],
            ["event_types.id"],
            name=op.f("fk_event_event_types_event_type_id_event_types"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint(
            "event_id", "event_type_id", name=op.f("pk_event_event_types")
        ),
    )
    op.create_index(
        op.f("ix_event_event_types_event_type_id"),
        "event_event_types",
        ["event_type_id"],
        unique=False,
    )
    op.create_table(
        "playlist_tracks",
        sa.Column("playlist_id", sa.Integer(), nullable=False),
        sa.Column("track_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column(
            "added_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "position >= 0", name=op.f("ck_playlist_tracks_position_nonnegative")
        ),
        sa.ForeignKeyConstraint(
            ["playlist_id"],
            ["playlists.id"],
            name=op.f("fk_playlist_tracks_playlist_id_playlists"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["track_id"],
            ["tracks.id"],
            name=op.f("fk_playlist_tracks_track_id_tracks"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "playlist_id", "track_id", name=op.f("pk_playlist_tracks")
        ),
        sa.UniqueConstraint(
            "playlist_id",
            "position",
            deferrable=True,
            initially="DEFERRED",
            name=op.f("uq_playlist_tracks_playlist_id"),
        ),
    )
    op.create_index(
        op.f("ix_playlist_tracks_track_id"),
        "playlist_tracks",
        ["track_id"],
        unique=False,
    )
    op.create_table(
        "reviews",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("rating_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "length(btrim(text)) > 0", name=op.f("ck_reviews_text_nonempty")
        ),
        sa.ForeignKeyConstraint(
            ["rating_id"],
            ["ratings.id"],
            name=op.f("fk_reviews_rating_id_ratings"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reviews")),
        sa.UniqueConstraint("rating_id", name=op.f("uq_reviews_rating_id")),
    )
    op.create_table(
        "favorites",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "entity_type",
            sa.Enum(
                "track",
                "album",
                "artist",
                "playlist",
                "event",
                "venue",
                "review",
                name="favorite_target",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("track_id", sa.Integer(), nullable=True),
        sa.Column("album_id", sa.Integer(), nullable=True),
        sa.Column("artist_id", sa.Integer(), nullable=True),
        sa.Column("playlist_id", sa.Integer(), nullable=True),
        sa.Column("event_id", sa.Integer(), nullable=True),
        sa.Column("venue_id", sa.Integer(), nullable=True),
        sa.Column("review_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "num_nonnulls(track_id, album_id, artist_id, playlist_id, event_id, venue_id, review_id) = 1 AND ((entity_type = 'track' AND track_id IS NOT NULL AND entity_id = track_id) OR (entity_type = 'album' AND album_id IS NOT NULL AND entity_id = album_id) OR (entity_type = 'artist' AND artist_id IS NOT NULL AND entity_id = artist_id) OR (entity_type = 'playlist' AND playlist_id IS NOT NULL AND entity_id = playlist_id) OR (entity_type = 'event' AND event_id IS NOT NULL AND entity_id = event_id) OR (entity_type = 'venue' AND venue_id IS NOT NULL AND entity_id = venue_id) OR (entity_type = 'review' AND review_id IS NOT NULL AND entity_id = review_id))",
            name=op.f("ck_favorites_target_consistent"),
        ),
        sa.CheckConstraint(
            "entity_id > 0", name=op.f("ck_favorites_entity_id_positive")
        ),
        sa.ForeignKeyConstraint(
            ["album_id"],
            ["albums.id"],
            name=op.f("fk_favorites_album_id_albums"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["artist_id"],
            ["artists.id"],
            name=op.f("fk_favorites_artist_id_artists"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["events.id"],
            name=op.f("fk_favorites_event_id_events"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["playlist_id"],
            ["playlists.id"],
            name=op.f("fk_favorites_playlist_id_playlists"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["review_id"],
            ["reviews.id"],
            name=op.f("fk_favorites_review_id_reviews"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["track_id"],
            ["tracks.id"],
            name=op.f("fk_favorites_track_id_tracks"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_favorites_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["venue_id"],
            ["venues.id"],
            name=op.f("fk_favorites_venue_id_venues"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_favorites")),
        sa.UniqueConstraint(
            "user_id", "entity_type", "entity_id", name=op.f("uq_favorites_user_id")
        ),
    )
    op.create_index(
        op.f("ix_favorites_album_id"), "favorites", ["album_id"], unique=False
    )
    op.create_index(
        op.f("ix_favorites_artist_id"), "favorites", ["artist_id"], unique=False
    )
    op.create_index(
        op.f("ix_favorites_event_id"), "favorites", ["event_id"], unique=False
    )
    op.create_index(
        op.f("ix_favorites_playlist_id"), "favorites", ["playlist_id"], unique=False
    )
    op.create_index(
        op.f("ix_favorites_review_id"), "favorites", ["review_id"], unique=False
    )
    op.create_index(
        "ix_favorites_target", "favorites", ["entity_type", "entity_id"], unique=False
    )
    op.create_index(
        op.f("ix_favorites_track_id"), "favorites", ["track_id"], unique=False
    )
    op.create_index(
        op.f("ix_favorites_venue_id"), "favorites", ["venue_id"], unique=False
    )
    op.add_column("albums", sa.Column("image_media_id", sa.Integer(), nullable=True))
    op.create_index(
        op.f("ix_albums_image_media_id"), "albums", ["image_media_id"], unique=False
    )
    op.create_foreign_key(
        op.f("fk_albums_image_media_id_media"),
        "albums",
        "media",
        ["image_media_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.add_column("artists", sa.Column("image_media_id", sa.Integer(), nullable=True))
    op.create_index(
        op.f("ix_artists_image_media_id"), "artists", ["image_media_id"], unique=False
    )
    op.create_foreign_key(
        op.f("fk_artists_image_media_id_media"),
        "artists",
        "media",
        ["image_media_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.add_column("tracks", sa.Column("audio_media_id", sa.Integer(), nullable=True))
    op.add_column("tracks", sa.Column("image_media_id", sa.Integer(), nullable=True))
    op.create_index(
        op.f("ix_tracks_audio_media_id"), "tracks", ["audio_media_id"], unique=False
    )
    op.create_index(
        op.f("ix_tracks_image_media_id"), "tracks", ["image_media_id"], unique=False
    )
    op.create_foreign_key(
        op.f("fk_tracks_image_media_id_media"),
        "tracks",
        "media",
        ["image_media_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        op.f("fk_tracks_audio_media_id_media"),
        "tracks",
        "media",
        ["audio_media_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.add_column("users", sa.Column("image_media_id", sa.Integer(), nullable=True))
    op.create_index(
        op.f("ix_users_image_media_id"), "users", ["image_media_id"], unique=False
    )
    op.create_foreign_key(
        op.f("fk_users_image_media_id_media"),
        "users",
        "media",
        ["image_media_id"],
        ["id"],
        ondelete="RESTRICT",
        use_alter=True,
    )
    op.add_column("venues", sa.Column("user_id", sa.Integer(), nullable=True))
    op.add_column("venues", sa.Column("image_media_id", sa.Integer(), nullable=True))
    op.create_index(
        op.f("ix_venues_image_media_id"), "venues", ["image_media_id"], unique=False
    )
    op.create_index(op.f("ix_venues_user_id"), "venues", ["user_id"], unique=False)
    op.create_foreign_key(
        op.f("fk_venues_image_media_id_media"),
        "venues",
        "media",
        ["image_media_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        op.f("fk_venues_user_id_users"),
        "venues",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.execute(
        "INSERT INTO event_types (id,name,slug) VALUES (1,'Concert','concert'),(2,'Jam','jam'),(3,'Find a group','find_a_group')"
    )
    op.execute("SELECT setval(pg_get_serial_sequence('event_types','id'),3,true)")
    op.execute(
        "INSERT INTO playlists (user_id,name,visibility,kind) SELECT id,'Liked','private','liked' FROM users"
    )


def downgrade() -> None:
    op.drop_constraint(op.f("fk_venues_user_id_users"), "venues", type_="foreignkey")
    op.drop_constraint(
        op.f("fk_venues_image_media_id_media"), "venues", type_="foreignkey"
    )
    op.drop_index(op.f("ix_venues_user_id"), table_name="venues")
    op.drop_index(op.f("ix_venues_image_media_id"), table_name="venues")
    op.drop_column("venues", "image_media_id")
    op.drop_column("venues", "user_id")
    op.drop_constraint(
        op.f("fk_users_image_media_id_media"), "users", type_="foreignkey"
    )
    op.drop_index(op.f("ix_users_image_media_id"), table_name="users")
    op.drop_column("users", "image_media_id")
    op.drop_constraint(
        op.f("fk_tracks_audio_media_id_media"), "tracks", type_="foreignkey"
    )
    op.drop_constraint(
        op.f("fk_tracks_image_media_id_media"), "tracks", type_="foreignkey"
    )
    op.drop_index(op.f("ix_tracks_image_media_id"), table_name="tracks")
    op.drop_index(op.f("ix_tracks_audio_media_id"), table_name="tracks")
    op.drop_column("tracks", "image_media_id")
    op.drop_column("tracks", "audio_media_id")
    op.drop_constraint(
        op.f("fk_artists_image_media_id_media"), "artists", type_="foreignkey"
    )
    op.drop_index(op.f("ix_artists_image_media_id"), table_name="artists")
    op.drop_column("artists", "image_media_id")
    op.drop_constraint(
        op.f("fk_albums_image_media_id_media"), "albums", type_="foreignkey"
    )
    op.drop_index(op.f("ix_albums_image_media_id"), table_name="albums")
    op.drop_column("albums", "image_media_id")
    op.drop_index(op.f("ix_favorites_venue_id"), table_name="favorites")
    op.drop_index(op.f("ix_favorites_track_id"), table_name="favorites")
    op.drop_index("ix_favorites_target", table_name="favorites")
    op.drop_index(op.f("ix_favorites_review_id"), table_name="favorites")
    op.drop_index(op.f("ix_favorites_playlist_id"), table_name="favorites")
    op.drop_index(op.f("ix_favorites_event_id"), table_name="favorites")
    op.drop_index(op.f("ix_favorites_artist_id"), table_name="favorites")
    op.drop_index(op.f("ix_favorites_album_id"), table_name="favorites")
    op.drop_table("favorites")
    op.drop_table("reviews")
    op.drop_index(op.f("ix_playlist_tracks_track_id"), table_name="playlist_tracks")
    op.drop_table("playlist_tracks")
    op.drop_index(
        op.f("ix_event_event_types_event_type_id"), table_name="event_event_types"
    )
    op.drop_table("event_event_types")
    op.drop_index(op.f("ix_follows_venue_id"), table_name="follows")
    op.drop_index(op.f("ix_follows_user_id"), table_name="follows")
    op.drop_index("ix_follows_target", table_name="follows")
    op.drop_index(op.f("ix_follows_artist_id"), table_name="follows")
    op.drop_table("follows")
    op.drop_index(op.f("ix_events_venue_id"), table_name="events")
    op.drop_index(op.f("ix_events_user_id"), table_name="events")
    op.drop_index("ix_events_coordinates", table_name="events")
    op.drop_index("ix_events_city_starts_at", table_name="events")
    op.drop_table("events")
    op.drop_index(
        "uq_playlists_liked_user",
        table_name="playlists",
        postgresql_where=sa.text("kind = 'liked'"),
    )
    op.drop_index(op.f("ix_playlists_user_id"), table_name="playlists")
    op.drop_index(op.f("ix_playlists_image_media_id"), table_name="playlists")
    op.drop_table("playlists")
    op.drop_index(op.f("ix_media_user_id"), table_name="media")
    op.drop_table("media")
    op.drop_table("event_types")
