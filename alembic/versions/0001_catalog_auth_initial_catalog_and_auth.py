"""Начальная схема каталога и авторизации.

Revision ID: 0001_catalog_auth
Revises:
"""

import sqlalchemy as sa

from alembic import op

revision = "0001_catalog_auth"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cities",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("region", sa.String(length=255), nullable=True),
        sa.Column("country", sa.String(length=255), nullable=False),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lng", sa.Float(), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
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
            "lat BETWEEN -90 AND 90", name=op.f("ck_cities_latitude_valid")
        ),
        sa.CheckConstraint(
            "length(btrim(country)) > 0", name=op.f("ck_cities_country_nonempty")
        ),
        sa.CheckConstraint(
            "length(btrim(name)) > 0", name=op.f("ck_cities_name_nonempty")
        ),
        sa.CheckConstraint(
            "length(btrim(timezone)) > 0", name=op.f("ck_cities_timezone_nonempty")
        ),
        sa.CheckConstraint(
            "lng BETWEEN -180 AND 180", name=op.f("ck_cities_longitude_valid")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cities")),
        sa.UniqueConstraint(
            "name",
            "region",
            "country",
            name=op.f("uq_cities_name"),
            postgresql_nulls_not_distinct=True,
        ),
    )
    op.create_index(op.f("ix_cities_name"), "cities", ["name"], unique=False)
    op.create_table(
        "genres",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.CheckConstraint(
            "slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'", name=op.f("ck_genres_slug_valid")
        ),
        sa.CheckConstraint(
            "length(btrim(name)) > 0", name=op.f("ck_genres_name_nonempty")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_genres")),
        sa.UniqueConstraint("slug", name=op.f("uq_genres_slug")),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column(
            "level",
            sa.Enum(
                "green",
                "experienced",
                "moderator",
                "admin",
                name="user_level",
                native_enum=False,
                create_constraint=True,
                length=64,
            ),
            server_default="green",
            nullable=False,
        ),
        sa.Column("weight", sa.Float(), server_default="1", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("city_id", sa.Integer(), nullable=True),
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
            "weight > 0 AND weight < 'Infinity'::float8",
            name=op.f("ck_users_weight_valid"),
        ),
        sa.CheckConstraint(
            "length(btrim(display_name)) > 0",
            name=op.f("ck_users_display_name_nonempty"),
        ),
        sa.CheckConstraint(
            "length(btrim(email)) > 0", name=op.f("ck_users_email_nonempty")
        ),
        sa.CheckConstraint(
            "length(password_hash) > 0", name=op.f("ck_users_password_hash_nonempty")
        ),
        sa.ForeignKeyConstraint(
            ["city_id"],
            ["cities.id"],
            name=op.f("fk_users_city_id_cities"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
    )
    op.create_index(op.f("ix_users_city_id"), "users", ["city_id"], unique=False)
    op.create_index(
        "uq_users_email_lower",
        "users",
        [sa.literal_column("lower(email)")],
        unique=True,
    )
    op.create_table(
        "venues",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("cover_url", sa.Text(), nullable=True),
        sa.Column("city_id", sa.Integer(), nullable=False),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lng", sa.Float(), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=True),
        sa.Column("website", sa.Text(), nullable=True),
        sa.Column("rating_sum", sa.Float(), server_default="0", nullable=False),
        sa.Column("rating_weight", sa.Float(), server_default="0", nullable=False),
        sa.Column("ratings_count", sa.Integer(), server_default="0", nullable=False),
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
            "rating_weight >= 0 AND rating_weight < 'Infinity'::float8",
            name=op.f("ck_venues_rating_weight_valid"),
        ),
        sa.CheckConstraint(
            "(ratings_count = 0 AND rating_weight = 0 AND rating_sum = 0) OR (ratings_count > 0 AND rating_weight > 0)",
            name=op.f("ck_venues_rating_aggregates_consistent"),
        ),
        sa.CheckConstraint(
            "capacity IS NULL OR capacity >= 0",
            name=op.f("ck_venues_capacity_nonnegative"),
        ),
        sa.CheckConstraint(
            "lat BETWEEN -90 AND 90", name=op.f("ck_venues_latitude_valid")
        ),
        sa.CheckConstraint(
            "length(btrim(name)) > 0", name=op.f("ck_venues_name_nonempty")
        ),
        sa.CheckConstraint(
            "lng BETWEEN -180 AND 180", name=op.f("ck_venues_longitude_valid")
        ),
        sa.CheckConstraint(
            "rating_sum >= rating_weight AND rating_sum <= 5 * rating_weight",
            name=op.f("ck_venues_rating_sum_valid"),
        ),
        sa.CheckConstraint(
            "ratings_count >= 0", name=op.f("ck_venues_ratings_count_nonnegative")
        ),
        sa.ForeignKeyConstraint(
            ["city_id"],
            ["cities.id"],
            name=op.f("fk_venues_city_id_cities"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_venues")),
    )
    op.create_index(op.f("ix_venues_city_id"), "venues", ["city_id"], unique=False)
    op.create_index(op.f("ix_venues_name"), "venues", ["name"], unique=False)
    op.create_table(
        "albums",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("cover_url", sa.Text(), nullable=True),
        sa.Column("release_date", sa.Date(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("rating_sum", sa.Float(), server_default="0", nullable=False),
        sa.Column("rating_weight", sa.Float(), server_default="0", nullable=False),
        sa.Column("ratings_count", sa.Integer(), server_default="0", nullable=False),
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
            "rating_weight >= 0 AND rating_weight < 'Infinity'::float8",
            name=op.f("ck_albums_rating_weight_valid"),
        ),
        sa.CheckConstraint(
            "(ratings_count = 0 AND rating_weight = 0 AND rating_sum = 0) OR (ratings_count > 0 AND rating_weight > 0)",
            name=op.f("ck_albums_rating_aggregates_consistent"),
        ),
        sa.CheckConstraint(
            "length(btrim(title)) > 0", name=op.f("ck_albums_title_nonempty")
        ),
        sa.CheckConstraint(
            "rating_sum >= rating_weight AND rating_sum <= 5 * rating_weight",
            name=op.f("ck_albums_rating_sum_valid"),
        ),
        sa.CheckConstraint(
            "ratings_count >= 0", name=op.f("ck_albums_ratings_count_nonnegative")
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_albums_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_albums")),
    )
    op.create_index(op.f("ix_albums_title"), "albums", ["title"], unique=False)
    op.create_index(op.f("ix_albums_user_id"), "albums", ["user_id"], unique=False)
    op.create_table(
        "artists",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("city_id", sa.Integer(), nullable=True),
        sa.Column("rating_sum", sa.Float(), server_default="0", nullable=False),
        sa.Column("rating_weight", sa.Float(), server_default="0", nullable=False),
        sa.Column("ratings_count", sa.Integer(), server_default="0", nullable=False),
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
            "rating_weight >= 0 AND rating_weight < 'Infinity'::float8",
            name=op.f("ck_artists_rating_weight_valid"),
        ),
        sa.CheckConstraint(
            "(ratings_count = 0 AND rating_weight = 0 AND rating_sum = 0) OR (ratings_count > 0 AND rating_weight > 0)",
            name=op.f("ck_artists_rating_aggregates_consistent"),
        ),
        sa.CheckConstraint(
            "length(btrim(name)) > 0", name=op.f("ck_artists_name_nonempty")
        ),
        sa.CheckConstraint(
            "rating_sum >= rating_weight AND rating_sum <= 5 * rating_weight",
            name=op.f("ck_artists_rating_sum_valid"),
        ),
        sa.CheckConstraint(
            "ratings_count >= 0", name=op.f("ck_artists_ratings_count_nonnegative")
        ),
        sa.ForeignKeyConstraint(
            ["city_id"],
            ["cities.id"],
            name=op.f("fk_artists_city_id_cities"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_artists_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_artists")),
    )
    op.create_index(op.f("ix_artists_city_id"), "artists", ["city_id"], unique=False)
    op.create_index(op.f("ix_artists_name"), "artists", ["name"], unique=False)
    op.create_index(op.f("ix_artists_user_id"), "artists", ["user_id"], unique=False)
    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("refresh_token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
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
            "expires_at > created_at", name=op.f("ck_auth_sessions_expiry_valid")
        ),
        sa.CheckConstraint(
            "revoked_at IS NULL OR revoked_at >= created_at",
            name=op.f("ck_auth_sessions_revocation_valid"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_auth_sessions_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_auth_sessions")),
        sa.UniqueConstraint(
            "refresh_token_hash", name=op.f("uq_auth_sessions_refresh_token_hash")
        ),
    )
    op.create_index(
        "ix_auth_sessions_expires_at", "auth_sessions", ["expires_at"], unique=False
    )
    op.create_index(
        op.f("ix_auth_sessions_user_id"), "auth_sessions", ["user_id"], unique=False
    )
    op.create_table(
        "user_favorite_genres",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("genre_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["genre_id"],
            ["genres.id"],
            name=op.f("fk_user_favorite_genres_genre_id_genres"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_user_favorite_genres_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "user_id", "genre_id", name=op.f("pk_user_favorite_genres")
        ),
    )
    op.create_index(
        op.f("ix_user_favorite_genres_genre_id"),
        "user_favorite_genres",
        ["genre_id"],
        unique=False,
    )
    op.create_table(
        "album_artists",
        sa.Column("album_id", sa.Integer(), nullable=False),
        sa.Column("artist_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["album_id"],
            ["albums.id"],
            name=op.f("fk_album_artists_album_id_albums"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["artist_id"],
            ["artists.id"],
            name=op.f("fk_album_artists_artist_id_artists"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("album_id", "artist_id", name=op.f("pk_album_artists")),
    )
    op.create_index(
        op.f("ix_album_artists_artist_id"), "album_artists", ["artist_id"], unique=False
    )
    op.create_table(
        "album_genres",
        sa.Column("album_id", sa.Integer(), nullable=False),
        sa.Column("genre_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["album_id"],
            ["albums.id"],
            name=op.f("fk_album_genres_album_id_albums"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["genre_id"],
            ["genres.id"],
            name=op.f("fk_album_genres_genre_id_genres"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("album_id", "genre_id", name=op.f("pk_album_genres")),
    )
    op.create_index(
        op.f("ix_album_genres_genre_id"), "album_genres", ["genre_id"], unique=False
    )
    op.create_table(
        "artist_genres",
        sa.Column("artist_id", sa.Integer(), nullable=False),
        sa.Column("genre_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["artist_id"],
            ["artists.id"],
            name=op.f("fk_artist_genres_artist_id_artists"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["genre_id"],
            ["genres.id"],
            name=op.f("fk_artist_genres_genre_id_genres"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("artist_id", "genre_id", name=op.f("pk_artist_genres")),
    )
    op.create_index(
        op.f("ix_artist_genres_genre_id"), "artist_genres", ["genre_id"], unique=False
    )
    op.create_table(
        "artist_members",
        sa.Column("artist_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "role", sa.String(length=64), server_default="member", nullable=False
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
            "length(btrim(role)) > 0", name=op.f("ck_artist_members_role_nonempty")
        ),
        sa.ForeignKeyConstraint(
            ["artist_id"],
            ["artists.id"],
            name=op.f("fk_artist_members_artist_id_artists"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_artist_members_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "artist_id", "user_id", "role", name=op.f("pk_artist_members")
        ),
    )
    op.create_index(
        op.f("ix_artist_members_user_id"), "artist_members", ["user_id"], unique=False
    )
    op.create_table(
        "tracks",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("duration", sa.Integer(), nullable=False),
        sa.Column("cover_url", sa.Text(), nullable=True),
        sa.Column("lyrics", sa.Text(), nullable=True),
        sa.Column("audio_key", sa.Text(), nullable=True),
        sa.Column("album_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("rating_sum", sa.Float(), server_default="0", nullable=False),
        sa.Column("rating_weight", sa.Float(), server_default="0", nullable=False),
        sa.Column("ratings_count", sa.Integer(), server_default="0", nullable=False),
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
            "rating_weight >= 0 AND rating_weight < 'Infinity'::float8",
            name=op.f("ck_tracks_rating_weight_valid"),
        ),
        sa.CheckConstraint(
            "(ratings_count = 0 AND rating_weight = 0 AND rating_sum = 0) OR (ratings_count > 0 AND rating_weight > 0)",
            name=op.f("ck_tracks_rating_aggregates_consistent"),
        ),
        sa.CheckConstraint("duration > 0", name=op.f("ck_tracks_duration_positive")),
        sa.CheckConstraint(
            "length(btrim(title)) > 0", name=op.f("ck_tracks_title_nonempty")
        ),
        sa.CheckConstraint(
            "rating_sum >= rating_weight AND rating_sum <= 5 * rating_weight",
            name=op.f("ck_tracks_rating_sum_valid"),
        ),
        sa.CheckConstraint(
            "ratings_count >= 0", name=op.f("ck_tracks_ratings_count_nonnegative")
        ),
        sa.ForeignKeyConstraint(
            ["album_id"],
            ["albums.id"],
            name=op.f("fk_tracks_album_id_albums"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_tracks_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tracks")),
    )
    op.create_index(op.f("ix_tracks_album_id"), "tracks", ["album_id"], unique=False)
    op.create_index(op.f("ix_tracks_title"), "tracks", ["title"], unique=False)
    op.create_index(op.f("ix_tracks_user_id"), "tracks", ["user_id"], unique=False)
    op.create_table(
        "track_artists",
        sa.Column("track_id", sa.Integer(), nullable=False),
        sa.Column("artist_id", sa.Integer(), nullable=False),
        sa.Column(
            "role", sa.String(length=64), server_default="primary", nullable=False
        ),
        sa.CheckConstraint(
            "length(btrim(role)) > 0", name=op.f("ck_track_artists_role_nonempty")
        ),
        sa.ForeignKeyConstraint(
            ["artist_id"],
            ["artists.id"],
            name=op.f("fk_track_artists_artist_id_artists"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["track_id"],
            ["tracks.id"],
            name=op.f("fk_track_artists_track_id_tracks"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "track_id", "artist_id", "role", name=op.f("pk_track_artists")
        ),
    )
    op.create_index(
        op.f("ix_track_artists_artist_id"), "track_artists", ["artist_id"], unique=False
    )
    op.create_table(
        "track_genres",
        sa.Column("track_id", sa.Integer(), nullable=False),
        sa.Column("genre_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["genre_id"],
            ["genres.id"],
            name=op.f("fk_track_genres_genre_id_genres"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["track_id"],
            ["tracks.id"],
            name=op.f("fk_track_genres_track_id_tracks"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("track_id", "genre_id", name=op.f("pk_track_genres")),
    )
    op.create_index(
        op.f("ix_track_genres_genre_id"), "track_genres", ["genre_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_track_genres_genre_id"), table_name="track_genres")
    op.drop_table("track_genres")
    op.drop_index(op.f("ix_track_artists_artist_id"), table_name="track_artists")
    op.drop_table("track_artists")
    op.drop_index(op.f("ix_tracks_user_id"), table_name="tracks")
    op.drop_index(op.f("ix_tracks_title"), table_name="tracks")
    op.drop_index(op.f("ix_tracks_album_id"), table_name="tracks")
    op.drop_table("tracks")
    op.drop_index(op.f("ix_artist_members_user_id"), table_name="artist_members")
    op.drop_table("artist_members")
    op.drop_index(op.f("ix_artist_genres_genre_id"), table_name="artist_genres")
    op.drop_table("artist_genres")
    op.drop_index(op.f("ix_album_genres_genre_id"), table_name="album_genres")
    op.drop_table("album_genres")
    op.drop_index(op.f("ix_album_artists_artist_id"), table_name="album_artists")
    op.drop_table("album_artists")
    op.drop_index(
        op.f("ix_user_favorite_genres_genre_id"), table_name="user_favorite_genres"
    )
    op.drop_table("user_favorite_genres")
    op.drop_index(op.f("ix_auth_sessions_user_id"), table_name="auth_sessions")
    op.drop_index("ix_auth_sessions_expires_at", table_name="auth_sessions")
    op.drop_table("auth_sessions")
    op.drop_index(op.f("ix_artists_user_id"), table_name="artists")
    op.drop_index(op.f("ix_artists_name"), table_name="artists")
    op.drop_index(op.f("ix_artists_city_id"), table_name="artists")
    op.drop_table("artists")
    op.drop_index(op.f("ix_albums_user_id"), table_name="albums")
    op.drop_index(op.f("ix_albums_title"), table_name="albums")
    op.drop_table("albums")
    op.drop_index(op.f("ix_venues_name"), table_name="venues")
    op.drop_index(op.f("ix_venues_city_id"), table_name="venues")
    op.drop_table("venues")
    op.drop_index("uq_users_email_lower", table_name="users")
    op.drop_index(op.f("ix_users_city_id"), table_name="users")
    op.drop_table("users")
    op.drop_table("genres")
    op.drop_index(op.f("ix_cities_name"), table_name="cities")
    op.drop_table("cities")
