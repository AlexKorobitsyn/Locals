// Сгенерировано из OpenAPI. Изменения вносятся через npm run api:generate.
export interface paths {
    "/api/v1/health/live": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Liveness */
        get: operations["liveness_api_v1_health_live_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/health/ready": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Readiness */
        get: operations["readiness_api_v1_health_ready_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/health/version": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Version */
        get: operations["version_api_v1_health_version_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/register": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Register */
        post: operations["register_api_v1_auth_register_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/login": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Login */
        post: operations["login_api_v1_auth_login_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/refresh": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Refresh */
        post: operations["refresh_api_v1_auth_refresh_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/logout": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Logout */
        post: operations["logout_api_v1_auth_logout_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/browser/login": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Browser Login */
        post: operations["browser_login_api_v1_auth_browser_login_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/browser/refresh": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Browser Refresh */
        post: operations["browser_refresh_api_v1_auth_browser_refresh_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/browser/logout": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Browser Logout */
        post: operations["browser_logout_api_v1_auth_browser_logout_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/me": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Me */
        get: operations["me_api_v1_me_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/users/{user_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Public Profile */
        get: operations["public_profile_api_v1_users__user_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/me/favorite-genres": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Favorite Genres */
        get: operations["get_favorite_genres_api_v1_me_favorite_genres_get"];
        /** Put Favorite Genres */
        put: operations["put_favorite_genres_api_v1_me_favorite_genres_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/me/artists": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** My Artists */
        get: operations["my_artists_api_v1_me_artists_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/me/albums": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** My Albums */
        get: operations["my_albums_api_v1_me_albums_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/me/tracks": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** My Tracks */
        get: operations["my_tracks_api_v1_me_tracks_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/artists": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Artists */
        get: operations["list_artists_api_v1_artists_get"];
        put?: never;
        /** Create */
        post: operations["create_api_v1_artists_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/artists/{artist_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Detail */
        get: operations["detail_api_v1_artists__artist_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Update */
        patch: operations["update_api_v1_artists__artist_id__patch"];
        trace?: never;
    };
    "/api/v1/albums": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Albums */
        get: operations["list_albums_api_v1_albums_get"];
        put?: never;
        /** Create */
        post: operations["create_api_v1_albums_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/albums/{album_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Detail */
        get: operations["detail_api_v1_albums__album_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Update */
        patch: operations["update_api_v1_albums__album_id__patch"];
        trace?: never;
    };
    "/api/v1/tracks": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Tracks */
        get: operations["list_tracks_api_v1_tracks_get"];
        put?: never;
        /** Create */
        post: operations["create_api_v1_tracks_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/tracks/{track_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Detail */
        get: operations["detail_api_v1_tracks__track_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Update */
        patch: operations["update_api_v1_tracks__track_id__patch"];
        trace?: never;
    };
    "/api/v1/genres": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Public Genres */
        get: operations["list_public_genres_api_v1_genres_get"];
        put?: never;
        /** Create */
        post: operations["create_api_v1_genres_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/ratings": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        /** Put */
        put: operations["put_api_v1_ratings_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/ratings/{target_type}/{target_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** Delete */
        delete: operations["delete_api_v1_ratings__target_type___target_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/cities": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Cities */
        get: operations["cities_api_v1_cities_get"];
        put?: never;
        /** Create */
        post: operations["create_api_v1_cities_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/venues": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Venues */
        get: operations["venues_api_v1_venues_get"];
        put?: never;
        /** Create */
        post: operations["create_api_v1_venues_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/venues/{venue_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Detail */
        get: operations["detail_api_v1_venues__venue_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Update */
        patch: operations["update_api_v1_venues__venue_id__patch"];
        trace?: never;
    };
    "/api/v1/event-types": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Types */
        get: operations["types_api_v1_event_types_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/events": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Events */
        get: operations["events_api_v1_events_get"];
        put?: never;
        /** Create */
        post: operations["create_api_v1_events_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/events/{event_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Detail */
        get: operations["detail_api_v1_events__event_id__get"];
        put?: never;
        post?: never;
        /** Remove */
        delete: operations["remove_api_v1_events__event_id__delete"];
        options?: never;
        head?: never;
        /** Update */
        patch: operations["update_api_v1_events__event_id__patch"];
        trace?: never;
    };
    "/api/v1/reviews": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Listing */
        get: operations["listing_api_v1_reviews_get"];
        put?: never;
        /** Create */
        post: operations["create_api_v1_reviews_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/reviews/{review_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Detail */
        get: operations["detail_api_v1_reviews__review_id__get"];
        put?: never;
        post?: never;
        /** Delete */
        delete: operations["delete_api_v1_reviews__review_id__delete"];
        options?: never;
        head?: never;
        /** Update */
        patch: operations["update_api_v1_reviews__review_id__patch"];
        trace?: never;
    };
    "/api/v1/playlists": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Listing */
        get: operations["listing_api_v1_playlists_get"];
        put?: never;
        /** Create */
        post: operations["create_api_v1_playlists_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/me/playlists": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Own */
        get: operations["own_api_v1_me_playlists_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/me/saved-playlists": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Saved */
        get: operations["saved_api_v1_me_saved_playlists_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/playlists/{playlist_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Detail */
        get: operations["detail_api_v1_playlists__playlist_id__get"];
        put?: never;
        post?: never;
        /** Delete */
        delete: operations["delete_api_v1_playlists__playlist_id__delete"];
        options?: never;
        head?: never;
        /** Update */
        patch: operations["update_api_v1_playlists__playlist_id__patch"];
        trace?: never;
    };
    "/api/v1/playlists/{playlist_id}/tracks": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Tracks */
        get: operations["tracks_api_v1_playlists__playlist_id__tracks_get"];
        put?: never;
        /** Add Track */
        post: operations["add_track_api_v1_playlists__playlist_id__tracks_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/playlists/{playlist_id}/tracks/{track_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** Remove Track */
        delete: operations["remove_track_api_v1_playlists__playlist_id__tracks__track_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/playlists/{playlist_id}/tracks/order": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        /** Reorder */
        put: operations["reorder_api_v1_playlists__playlist_id__tracks_order_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/favorites": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        /** Put */
        put: operations["put_api_v1_favorites_put"];
        /** Put */
        post: operations["put_api_v1_favorites_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/favorites/{entity_type}/{entity_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** Remove */
        delete: operations["remove_api_v1_favorites__entity_type___entity_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/me/favorites": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Listing */
        get: operations["listing_api_v1_me_favorites_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/follows": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        /** Put */
        put: operations["put_api_v1_follows_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/follows/{target_type}/{target_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** Remove */
        delete: operations["remove_api_v1_follows__target_type___target_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/me/following": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Listing */
        get: operations["listing_api_v1_me_following_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/me/feed": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Feed */
        get: operations["feed_api_v1_me_feed_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/media/images": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Image Upload */
        post: operations["image_upload_api_v1_media_images_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/media/audio": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Audio Upload */
        post: operations["audio_upload_api_v1_media_audio_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/media/{media_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Metadata */
        get: operations["metadata_api_v1_media__media_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/media/{media_id}/content": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Content */
        get: operations["content_api_v1_media__media_id__content_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/images/{target_type}/{target_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        /** Image Attach */
        put: operations["image_attach_api_v1_images__target_type___target_id__put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/tracks/{track_id}/audio": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Track Audio */
        get: operations["track_audio_api_v1_tracks__track_id__audio_get"];
        /** Audio Attach */
        put: operations["audio_attach_api_v1_tracks__track_id__audio_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/tracks/{track_id}/playback": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Track Playback */
        get: operations["track_playback_api_v1_tracks__track_id__playback_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/recommendations/tracks": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Tracks */
        get: operations["tracks_api_v1_recommendations_tracks_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
}
export type webhooks = Record<string, never>;
export interface components {
    schemas: {
        /** ActivityOut */
        ActivityOut: {
            /** Id */
            id: number;
            actor?: components["schemas"]["UserShort"] | null;
            /** Action */
            action: string;
            /** Target Type */
            target_type: string;
            /** Target Id */
            target_id: number;
            /** Payload */
            payload: {
                [key: string]: unknown;
            };
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /** AlbumCreate */
        AlbumCreate: {
            /** Title */
            title: string;
            /** Cover Url */
            cover_url?: string | null;
            /** Release Date */
            release_date?: string | null;
            /** Artist Ids */
            artist_ids: number[];
            /** Genre Ids */
            genre_ids?: number[];
        };
        /** AlbumOut */
        AlbumOut: {
            /**
             * Ratings Count
             * @default 0
             */
            ratings_count: number;
            /** My Rating */
            my_rating?: number | null;
            /**
             * Likes Count
             * @default 0
             */
            likes_count: number;
            /**
             * Is Liked By Me
             * @default false
             */
            is_liked_by_me: boolean;
            /** Id */
            id: number;
            /** Title */
            title: string;
            /** Cover Url */
            cover_url?: string | null;
            /** Release Date */
            release_date?: string | null;
            /** Artists */
            artists?: components["schemas"]["ArtistShort"][];
            /** Genres */
            genres?: components["schemas"]["GenreOut"][];
            /**
             * Tracks Count
             * @default 0
             */
            tracks_count: number;
            /**
             * Duration
             * @default 0
             */
            duration: number;
            /** User Id */
            user_id?: number | null;
            /**
             * Is Owner
             * @default false
             */
            is_owner: boolean;
            /** Rating Avg */
            readonly rating_avg: number | null;
        };
        /** AlbumRatedShort */
        AlbumRatedShort: {
            /**
             * Ratings Count
             * @default 0
             */
            ratings_count: number;
            /** My Rating */
            my_rating?: number | null;
            /**
             * Likes Count
             * @default 0
             */
            likes_count: number;
            /**
             * Is Liked By Me
             * @default false
             */
            is_liked_by_me: boolean;
            /** Id */
            id: number;
            /** Title */
            title: string;
            /** Cover Url */
            cover_url?: string | null;
            /** Release Date */
            release_date?: string | null;
            /** Artists */
            artists?: components["schemas"]["ArtistShort"][];
            /** Rating Avg */
            readonly rating_avg: number | null;
        };
        /** AlbumShort */
        AlbumShort: {
            /** Id */
            id: number;
            /** Title */
            title: string;
            /** Cover Url */
            cover_url?: string | null;
            /** Release Date */
            release_date?: string | null;
            /** Artists */
            artists?: components["schemas"]["ArtistShort"][];
        };
        /** AlbumUpdate */
        AlbumUpdate: {
            /** Title */
            title?: string | null;
            /** Cover Url */
            cover_url?: string | null;
            /** Release Date */
            release_date?: string | null;
            /** Artist Ids */
            artist_ids?: number[] | null;
            /** Genre Ids */
            genre_ids?: number[] | null;
        };
        /** ArtistCreate */
        ArtistCreate: {
            /** Name */
            name: string;
            /** Bio */
            bio?: string | null;
            /** Image Url */
            image_url?: string | null;
            /** City Id */
            city_id?: number | null;
            /** Genre Ids */
            genre_ids?: number[];
        };
        /** ArtistOut */
        ArtistOut: {
            /**
             * Ratings Count
             * @default 0
             */
            ratings_count: number;
            /** My Rating */
            my_rating?: number | null;
            /**
             * Likes Count
             * @default 0
             */
            likes_count: number;
            /**
             * Is Liked By Me
             * @default false
             */
            is_liked_by_me: boolean;
            /** Id */
            id: number;
            /** Name */
            name: string;
            /** Image Url */
            image_url?: string | null;
            /** Bio */
            bio?: string | null;
            city?: components["schemas"]["CityOut"] | null;
            /** Genres */
            genres?: components["schemas"]["GenreOut"][];
            /**
             * Albums Count
             * @default 0
             */
            albums_count: number;
            /**
             * Tracks Count
             * @default 0
             */
            tracks_count: number;
            /**
             * Followers Count
             * @default 0
             */
            followers_count: number;
            /** User Id */
            user_id?: number | null;
            /**
             * Is Owner
             * @default false
             */
            is_owner: boolean;
            /**
             * Is Followed By Me
             * @default false
             */
            is_followed_by_me: boolean;
            /** Rating Avg */
            readonly rating_avg: number | null;
        };
        /** ArtistRatedShort */
        ArtistRatedShort: {
            /**
             * Ratings Count
             * @default 0
             */
            ratings_count: number;
            /** My Rating */
            my_rating?: number | null;
            /**
             * Likes Count
             * @default 0
             */
            likes_count: number;
            /**
             * Is Liked By Me
             * @default false
             */
            is_liked_by_me: boolean;
            /** Id */
            id: number;
            /** Name */
            name: string;
            /** Image Url */
            image_url?: string | null;
            /** Rating Avg */
            readonly rating_avg: number | null;
        };
        /** ArtistShort */
        ArtistShort: {
            /** Id */
            id: number;
            /** Name */
            name: string;
            /** Image Url */
            image_url?: string | null;
        };
        /** ArtistUpdate */
        ArtistUpdate: {
            /** Name */
            name?: string | null;
            /** Bio */
            bio?: string | null;
            /** Image Url */
            image_url?: string | null;
            /** City Id */
            city_id?: number | null;
            /** Genre Ids */
            genre_ids?: number[] | null;
        };
        /** Body_audio_upload_api_v1_media_audio_post */
        Body_audio_upload_api_v1_media_audio_post: {
            /** File */
            file: string;
        };
        /** Body_image_upload_api_v1_media_images_post */
        Body_image_upload_api_v1_media_images_post: {
            /** File */
            file: string;
        };
        /** BrowserToken */
        BrowserToken: {
            /** Access Token */
            access_token: string;
            /**
             * Token Type
             * @default bearer
             * @constant
             */
            token_type: "bearer";
            /** Expires In */
            expires_in: number;
            /** User Id */
            user_id: number;
            /**
             * Session Id
             * Format: uuid
             */
            session_id: string;
        };
        /** CityCreate */
        CityCreate: {
            /** Name */
            name: string;
            /** Region */
            region?: string | null;
            /** Country */
            country: string;
            /** Lat */
            lat: number;
            /** Lng */
            lng: number;
            /** Timezone */
            timezone: string;
        };
        /** CityOut */
        CityOut: {
            /** Id */
            id: number;
            /** Name */
            name: string;
            /** Region */
            region?: string | null;
            /** Country */
            country: string;
            /** Lat */
            lat: number;
            /** Lng */
            lng: number;
            /** Timezone */
            timezone: string;
        };
        /** CityShort */
        CityShort: {
            /** Id */
            id: number;
            /** Name */
            name: string;
        };
        /** EventCreate */
        EventCreate: {
            /** Name */
            name: string;
            /** Venue Id */
            venue_id?: number | null;
            /** City Id */
            city_id?: number | null;
            /** Lat */
            lat?: number | null;
            /** Lng */
            lng?: number | null;
            /** Description */
            description?: string | null;
            /**
             * Starts At
             * Format: date-time
             */
            starts_at: string;
            /** Stop At */
            stop_at?: string | null;
            /** Type Event Ids */
            type_event_ids?: number[];
        };
        /** EventOut */
        EventOut: {
            /** Id */
            id: number;
            /** Name */
            name: string;
            venue?: components["schemas"]["VenueShort"] | null;
            /**
             * Starts At
             * Format: date-time
             */
            starts_at: string;
            /** Stop At */
            stop_at?: string | null;
            /** Type Event */
            type_event?: components["schemas"]["EventType"][];
            city?: components["schemas"]["CityShort"] | null;
            /** Lat */
            lat?: number | null;
            /** Lng */
            lng?: number | null;
            /** Description */
            description?: string | null;
            /** User Id */
            user_id?: number | null;
            /**
             * Is Owner
             * @default false
             */
            is_owner: boolean;
            /**
             * Is Liked By Me
             * @default false
             */
            is_liked_by_me: boolean;
            /**
             * Likes Count
             * @default 0
             */
            likes_count: number;
        };
        /** EventType */
        EventType: {
            /** Id */
            id: number;
            /** Name */
            name: string;
            /** Slug */
            slug: string;
        };
        /** EventUpdate */
        EventUpdate: {
            /** Name */
            name?: string | null;
            /** Venue Id */
            venue_id?: number | null;
            /** City Id */
            city_id?: number | null;
            /** Lat */
            lat?: number | null;
            /** Lng */
            lng?: number | null;
            /** Description */
            description?: string | null;
            /** Starts At */
            starts_at?: string | null;
            /** Stop At */
            stop_at?: string | null;
            /** Type Event Ids */
            type_event_ids?: number[] | null;
        };
        /** FavoriteCreate */
        FavoriteCreate: {
            entity_type: components["schemas"]["FavoriteTarget"];
            /** Entity Id */
            entity_id: number;
        };
        /** FavoriteGenresPut */
        FavoriteGenresPut: {
            /** Genre Ids */
            genre_ids: number[];
        };
        /** FavoriteRead */
        FavoriteRead: {
            /** Id */
            id: number;
            /** User Id */
            user_id: number;
            entity_type: components["schemas"]["FavoriteTarget"];
            /** Entity Id */
            entity_id: number;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /**
         * FavoriteTarget
         * @enum {string}
         */
        FavoriteTarget: "track" | "album" | "artist" | "playlist" | "event" | "venue" | "review";
        /** FollowCreate */
        FollowCreate: {
            target_type: components["schemas"]["FollowTarget"];
            /** Target Id */
            target_id: number;
        };
        /** FollowOut */
        FollowOut: {
            /** Id */
            id: number;
            /** Follower Id */
            follower_id: number;
            target_type: components["schemas"]["FollowTarget"];
            /** Target Id */
            target_id: number;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /**
         * FollowTarget
         * @enum {string}
         */
        FollowTarget: "user" | "artist" | "venue";
        /** GenreCreate */
        GenreCreate: {
            /** Name */
            name: string;
            /** Slug */
            slug: string;
        };
        /** GenreOut */
        GenreOut: {
            /** Id */
            id: number;
            /** Slug */
            slug: string;
            /** Name */
            name: string;
        };
        /** GenrePreference */
        GenrePreference: {
            genre: components["schemas"]["GenreOut"];
            /** Affinity */
            affinity: number;
            /** Ratings Count */
            ratings_count: number;
        };
        /** HTTPValidationError */
        HTTPValidationError: {
            /** Detail */
            detail?: components["schemas"]["ValidationError"][];
        };
        /** HealthOut */
        HealthOut: {
            /**
             * Status
             * @default ok
             * @constant
             */
            status: "ok";
        };
        /** LoginInput */
        LoginInput: {
            /**
             * Email
             * Format: email
             */
            email: string;
            /**
             * Password
             * Format: password
             */
            password: string;
        };
        /** MediaAttach */
        MediaAttach: {
            /** Media Id */
            media_id: number;
        };
        /** MediaOut */
        MediaOut: {
            /** Id */
            id: number;
            /**
             * Kind
             * @enum {string}
             */
            kind: "audio" | "image";
            /** Filename */
            filename: string;
            /** Content Type */
            content_type: string;
            /** Size */
            size: number;
            /** Sha256 */
            sha256: string;
            /** Duration */
            duration?: number | null;
            /** Width */
            width?: number | null;
            /** Height */
            height?: number | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /** Page[ActivityOut] */
        Page_ActivityOut_: {
            /** Items */
            items: components["schemas"]["ActivityOut"][];
            /** Total */
            total: number;
            /**
             * Limit
             * @default 20
             */
            limit: number;
            /**
             * Offset
             * @default 0
             */
            offset: number;
        };
        /** Page[AlbumRatedShort] */
        Page_AlbumRatedShort_: {
            /** Items */
            items: components["schemas"]["AlbumRatedShort"][];
            /** Total */
            total: number;
            /**
             * Limit
             * @default 20
             */
            limit: number;
            /**
             * Offset
             * @default 0
             */
            offset: number;
        };
        /** Page[ArtistRatedShort] */
        Page_ArtistRatedShort_: {
            /** Items */
            items: components["schemas"]["ArtistRatedShort"][];
            /** Total */
            total: number;
            /**
             * Limit
             * @default 20
             */
            limit: number;
            /**
             * Offset
             * @default 0
             */
            offset: number;
        };
        /** Page[CityOut] */
        Page_CityOut_: {
            /** Items */
            items: components["schemas"]["CityOut"][];
            /** Total */
            total: number;
            /**
             * Limit
             * @default 20
             */
            limit: number;
            /**
             * Offset
             * @default 0
             */
            offset: number;
        };
        /** Page[EventOut] */
        Page_EventOut_: {
            /** Items */
            items: components["schemas"]["EventOut"][];
            /** Total */
            total: number;
            /**
             * Limit
             * @default 20
             */
            limit: number;
            /**
             * Offset
             * @default 0
             */
            offset: number;
        };
        /** Page[FavoriteRead] */
        Page_FavoriteRead_: {
            /** Items */
            items: components["schemas"]["FavoriteRead"][];
            /** Total */
            total: number;
            /**
             * Limit
             * @default 20
             */
            limit: number;
            /**
             * Offset
             * @default 0
             */
            offset: number;
        };
        /** Page[FollowOut] */
        Page_FollowOut_: {
            /** Items */
            items: components["schemas"]["FollowOut"][];
            /** Total */
            total: number;
            /**
             * Limit
             * @default 20
             */
            limit: number;
            /**
             * Offset
             * @default 0
             */
            offset: number;
        };
        /** Page[GenreOut] */
        Page_GenreOut_: {
            /** Items */
            items: components["schemas"]["GenreOut"][];
            /** Total */
            total: number;
            /**
             * Limit
             * @default 20
             */
            limit: number;
            /**
             * Offset
             * @default 0
             */
            offset: number;
        };
        /** Page[PlaylistShort] */
        Page_PlaylistShort_: {
            /** Items */
            items: components["schemas"]["PlaylistShort"][];
            /** Total */
            total: number;
            /**
             * Limit
             * @default 20
             */
            limit: number;
            /**
             * Offset
             * @default 0
             */
            offset: number;
        };
        /** Page[PlaylistTrackItem] */
        Page_PlaylistTrackItem_: {
            /** Items */
            items: components["schemas"]["PlaylistTrackItem"][];
            /** Total */
            total: number;
            /**
             * Limit
             * @default 20
             */
            limit: number;
            /**
             * Offset
             * @default 0
             */
            offset: number;
        };
        /** Page[ReviewOut] */
        Page_ReviewOut_: {
            /** Items */
            items: components["schemas"]["ReviewOut"][];
            /** Total */
            total: number;
            /**
             * Limit
             * @default 20
             */
            limit: number;
            /**
             * Offset
             * @default 0
             */
            offset: number;
        };
        /** Page[TrackRatedShort] */
        Page_TrackRatedShort_: {
            /** Items */
            items: components["schemas"]["TrackRatedShort"][];
            /** Total */
            total: number;
            /**
             * Limit
             * @default 20
             */
            limit: number;
            /**
             * Offset
             * @default 0
             */
            offset: number;
        };
        /** Page[VenueRatedShort] */
        Page_VenueRatedShort_: {
            /** Items */
            items: components["schemas"]["VenueRatedShort"][];
            /** Total */
            total: number;
            /**
             * Limit
             * @default 20
             */
            limit: number;
            /**
             * Offset
             * @default 0
             */
            offset: number;
        };
        /** PlaybackOut */
        PlaybackOut: {
            /** Url */
            url: string;
            /** Expires In */
            expires_in: number;
            /** Content Type */
            content_type: string;
            /** Duration */
            duration: number;
        };
        /** PlaylistCreate */
        PlaylistCreate: {
            /** Name */
            name: string;
            /** Description */
            description?: string | null;
            /**
             * Visibility
             * @default private
             * @enum {string}
             */
            visibility: "public" | "private";
            /** Cover Url */
            cover_url?: string | null;
        };
        /**
         * PlaylistKind
         * @enum {string}
         */
        PlaylistKind: "custom" | "liked";
        /** PlaylistOut */
        PlaylistOut: {
            /** Id */
            id: number;
            /** Name */
            name: string;
            /** Cover Url */
            cover_url?: string | null;
            /**
             * Tracks Count
             * @default 0
             */
            tracks_count: number;
            /**
             * Likes Count
             * @default 0
             */
            likes_count: number;
            /** @default custom */
            kind: components["schemas"]["PlaylistKind"];
            /**
             * Visibility
             * @enum {string}
             */
            visibility: "public" | "private";
            /**
             * Is Owner
             * @default false
             */
            is_owner: boolean;
            /**
             * Is Liked By Me
             * @default false
             */
            is_liked_by_me: boolean;
            /** Description */
            description?: string | null;
            owner: components["schemas"]["UserShort"];
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
        };
        /** PlaylistReorder */
        PlaylistReorder: {
            /** Track Ids */
            track_ids: number[];
        };
        /** PlaylistShort */
        PlaylistShort: {
            /** Id */
            id: number;
            /** Name */
            name: string;
            /** Cover Url */
            cover_url?: string | null;
            /**
             * Tracks Count
             * @default 0
             */
            tracks_count: number;
            /**
             * Likes Count
             * @default 0
             */
            likes_count: number;
            /** @default custom */
            kind: components["schemas"]["PlaylistKind"];
            /**
             * Visibility
             * @default private
             * @enum {string}
             */
            visibility: "public" | "private";
            /**
             * Is Owner
             * @default false
             */
            is_owner: boolean;
            /**
             * Is Liked By Me
             * @default false
             */
            is_liked_by_me: boolean;
        };
        /** PlaylistTrackAdd */
        PlaylistTrackAdd: {
            /** Track Id */
            track_id: number;
            /** Position */
            position?: number | null;
        };
        /** PlaylistTrackItem */
        PlaylistTrackItem: {
            track: components["schemas"]["TrackRatedShort"];
            /** Position */
            position: number;
            /**
             * Added At
             * Format: date-time
             */
            added_at: string;
        };
        /** PlaylistUpdate */
        PlaylistUpdate: {
            /** Name */
            name?: string | null;
            /** Description */
            description?: string | null;
            /** Visibility */
            visibility?: ("public" | "private") | null;
            /** Cover Url */
            cover_url?: string | null;
        };
        /** RatingPut */
        RatingPut: {
            target_type: components["schemas"]["RatingTarget"];
            /** Target Id */
            target_id: number;
            /** Value */
            value: number;
        };
        /** RatingResult */
        RatingResult: {
            /**
             * Ratings Count
             * @default 0
             */
            ratings_count: number;
            /** My Rating */
            my_rating?: number | null;
            target_type: components["schemas"]["RatingTarget"];
            /** Target Id */
            target_id: number;
            /** Rating Avg */
            readonly rating_avg: number | null;
        };
        /**
         * RatingTarget
         * @enum {string}
         */
        RatingTarget: "track" | "album" | "artist" | "venue";
        /** ReadinessOut */
        ReadinessOut: {
            /**
             * Status
             * @enum {string}
             */
            status: "ok" | "unavailable";
            /**
             * Database
             * @enum {string}
             */
            database: "ok" | "unavailable";
        };
        /** RecommendationPage */
        RecommendationPage: {
            /** Items */
            items: components["schemas"]["RecommendedTrack"][];
            /** Total */
            total: number;
            /**
             * Limit
             * @default 20
             */
            limit: number;
            /**
             * Offset
             * @default 0
             */
            offset: number;
            /**
             * Mode
             * @enum {string}
             */
            mode: "popular" | "personalized";
            /**
             * Algorithm Version
             * @default rules_v1
             * @constant
             */
            algorithm_version: "rules_v1";
        };
        /** RecommendationScore */
        RecommendationScore: {
            /** Favorite Genre Score */
            favorite_genre_score: number;
            /** Rated Genre Score */
            rated_genre_score: number;
            /** Quality Score */
            quality_score: number;
            /** Total */
            total: number;
        };
        /** RecommendedTrack */
        RecommendedTrack: {
            /**
             * Ratings Count
             * @default 0
             */
            ratings_count: number;
            /** My Rating */
            my_rating?: number | null;
            /**
             * Likes Count
             * @default 0
             */
            likes_count: number;
            /**
             * Is Liked By Me
             * @default false
             */
            is_liked_by_me: boolean;
            /** Id */
            id: number;
            /** Title */
            title: string;
            /** Duration */
            duration: number;
            /** Cover Url */
            cover_url?: string | null;
            /** Artists */
            artists?: components["schemas"]["ArtistShort"][];
            /** Genres */
            genres?: components["schemas"]["GenreOut"][];
            /**
             * Is Playable
             * @default false
             */
            is_playable: boolean;
            /** Matched Favorite Genres */
            matched_favorite_genres?: components["schemas"]["GenreOut"][];
            /** Genre Preferences */
            genre_preferences?: components["schemas"]["GenrePreference"][];
            score: components["schemas"]["RecommendationScore"];
            /** Reasons */
            reasons: ("favorite_genres" | "high_rated_genres" | "low_rated_genres" | "community_rating" | "catalog_fallback")[];
            /** Rating Avg */
            readonly rating_avg: number | null;
        };
        /** RefreshInput */
        RefreshInput: {
            /**
             * Refresh Token
             * Format: password
             */
            refresh_token: string;
        };
        /** RegisterInput */
        RegisterInput: {
            /**
             * Email
             * Format: email
             */
            email: string;
            /**
             * Password
             * Format: password
             */
            password: string;
            /** Display Name */
            display_name: string;
        };
        /** ReviewCreate */
        ReviewCreate: {
            target_type: components["schemas"]["RatingTarget"];
            /** Target Id */
            target_id: number;
            /** Title */
            title?: string | null;
            /** Text */
            text: string;
        };
        /** ReviewOut */
        ReviewOut: {
            /** Id */
            id: number;
            /** Title */
            title?: string | null;
            /** Rating */
            rating: number;
            /**
             * Likes Count
             * @default 0
             */
            likes_count: number;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Text */
            text: string;
            author: components["schemas"]["UserShort"];
            /**
             * Target Type
             * @enum {string}
             */
            target_type: "track" | "album" | "artist" | "venue";
            /** Target Id */
            target_id: number;
            /**
             * Is Liked By Me
             * @default false
             */
            is_liked_by_me: boolean;
            /**
             * Is Owner
             * @default false
             */
            is_owner: boolean;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
        };
        /** ReviewUpdate */
        ReviewUpdate: {
            /** Title */
            title?: string | null;
            /** Text */
            text?: string | null;
        };
        /** TokenPair */
        TokenPair: {
            /** Access Token */
            access_token: string;
            /** Refresh Token */
            refresh_token: string;
            /**
             * Token Type
             * @default bearer
             * @constant
             */
            token_type: "bearer";
            /** Expires In */
            expires_in: number;
            /** Refresh Expires In */
            refresh_expires_in: number;
        };
        /** TrackArtistInput */
        TrackArtistInput: {
            /** Artist Id */
            artist_id: number;
            /**
             * Role
             * @default primary
             */
            role: string;
        };
        /** TrackArtistOut */
        TrackArtistOut: {
            artist: components["schemas"]["ArtistShort"];
            /** Role */
            role: string;
        };
        /** TrackCreate */
        TrackCreate: {
            /** Title */
            title: string;
            /** Album Id */
            album_id?: number | null;
            /** Artist Ids */
            artist_ids?: number[];
            /** Artist Credits */
            artist_credits?: components["schemas"]["TrackArtistInput"][];
            /** Duration */
            duration: number;
            /** Cover Url */
            cover_url?: string | null;
            /** Lyrics */
            lyrics?: string | null;
            /** Genre Ids */
            genre_ids?: number[];
        };
        /** TrackOut */
        TrackOut: {
            /**
             * Ratings Count
             * @default 0
             */
            ratings_count: number;
            /** My Rating */
            my_rating?: number | null;
            /**
             * Likes Count
             * @default 0
             */
            likes_count: number;
            /**
             * Is Liked By Me
             * @default false
             */
            is_liked_by_me: boolean;
            /** Id */
            id: number;
            /** Title */
            title: string;
            /** Duration */
            duration: number;
            /** Cover Url */
            cover_url?: string | null;
            album?: components["schemas"]["AlbumShort"] | null;
            /** Artists */
            artists?: components["schemas"]["ArtistShort"][];
            /** Genres */
            genres?: components["schemas"]["GenreOut"][];
            /** Lyrics */
            lyrics?: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Artist Credits */
            artist_credits?: components["schemas"]["TrackArtistOut"][];
            /** User Id */
            user_id?: number | null;
            /**
             * Is Owner
             * @default false
             */
            is_owner: boolean;
            /** Audio Media Id */
            audio_media_id?: number | null;
            /** Rating Avg */
            readonly rating_avg: number | null;
        };
        /** TrackRatedShort */
        TrackRatedShort: {
            /**
             * Ratings Count
             * @default 0
             */
            ratings_count: number;
            /** My Rating */
            my_rating?: number | null;
            /**
             * Likes Count
             * @default 0
             */
            likes_count: number;
            /**
             * Is Liked By Me
             * @default false
             */
            is_liked_by_me: boolean;
            /** Id */
            id: number;
            /** Title */
            title: string;
            /** Duration */
            duration: number;
            /** Cover Url */
            cover_url?: string | null;
            /** Rating Avg */
            readonly rating_avg: number | null;
        };
        /** TrackUpdate */
        TrackUpdate: {
            /** Title */
            title?: string | null;
            /** Album Id */
            album_id?: number | null;
            /** Artist Ids */
            artist_ids?: number[] | null;
            /** Artist Credits */
            artist_credits?: components["schemas"]["TrackArtistInput"][] | null;
            /** Duration */
            duration?: number | null;
            /** Cover Url */
            cover_url?: string | null;
            /** Lyrics */
            lyrics?: string | null;
            /** Genre Ids */
            genre_ids?: number[] | null;
        };
        /** UserMe */
        UserMe: {
            /** Id */
            id: number;
            /** Display Name */
            display_name: string;
            /** Avatar Url */
            avatar_url?: string | null;
            /** Bio */
            bio?: string | null;
            /**
             * Type
             * @enum {string}
             */
            type: "user" | "artist";
            city?: components["schemas"]["CityOut"] | null;
            /**
             * Followers Count
             * @default 0
             */
            followers_count: number;
            /**
             * Following Count
             * @default 0
             */
            following_count: number;
            /**
             * Is Followed By Me
             * @default false
             */
            is_followed_by_me: boolean;
            /** Email */
            email: string;
            /**
             * Level
             * @enum {string}
             */
            level: "green" | "experienced" | "moderator" | "admin";
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /** UserOut */
        UserOut: {
            /** Id */
            id: number;
            /** Display Name */
            display_name: string;
            /** Avatar Url */
            avatar_url?: string | null;
            /** Bio */
            bio?: string | null;
            /**
             * Type
             * @enum {string}
             */
            type: "user" | "artist";
            city?: components["schemas"]["CityOut"] | null;
            /**
             * Followers Count
             * @default 0
             */
            followers_count: number;
            /**
             * Following Count
             * @default 0
             */
            following_count: number;
            /**
             * Is Followed By Me
             * @default false
             */
            is_followed_by_me: boolean;
        };
        /** UserShort */
        UserShort: {
            /** Id */
            id: number;
            /** Display Name */
            display_name: string;
            /** Avatar Url */
            avatar_url?: string | null;
        };
        /** ValidationError */
        ValidationError: {
            /** Location */
            loc: (string | number)[];
            /** Message */
            msg: string;
            /** Error Type */
            type: string;
            /** Input */
            input?: unknown;
            /** Context */
            ctx?: Record<string, never>;
        };
        /** VenueCreate */
        VenueCreate: {
            /** Name */
            name: string;
            /** City Id */
            city_id: number;
            /** Lat */
            lat: number;
            /** Lng */
            lng: number;
            /** Description */
            description?: string | null;
            /** Address */
            address?: string | null;
            /** Capacity */
            capacity?: number | null;
            /** Website */
            website?: string | null;
            /** Cover Url */
            cover_url?: string | null;
        };
        /** VenueOut */
        VenueOut: {
            /**
             * Ratings Count
             * @default 0
             */
            ratings_count: number;
            /** My Rating */
            my_rating?: number | null;
            /**
             * Likes Count
             * @default 0
             */
            likes_count: number;
            /**
             * Is Liked By Me
             * @default false
             */
            is_liked_by_me: boolean;
            /** Id */
            id: number;
            /** Name */
            name: string;
            /** Cover Url */
            cover_url?: string | null;
            city: components["schemas"]["CityShort"];
            /** Description */
            description?: string | null;
            /** Address */
            address?: string | null;
            /** Lat */
            lat: number;
            /** Lng */
            lng: number;
            /** Capacity */
            capacity?: number | null;
            /** Website */
            website?: string | null;
            /**
             * Events Count
             * @default 0
             */
            events_count: number;
            /**
             * Followers Count
             * @default 0
             */
            followers_count: number;
            /** User Id */
            user_id?: number | null;
            /**
             * Is Owner
             * @default false
             */
            is_owner: boolean;
            /**
             * Is Followed By Me
             * @default false
             */
            is_followed_by_me: boolean;
            /** Rating Avg */
            readonly rating_avg: number | null;
        };
        /** VenueRatedShort */
        VenueRatedShort: {
            /**
             * Ratings Count
             * @default 0
             */
            ratings_count: number;
            /** My Rating */
            my_rating?: number | null;
            /**
             * Likes Count
             * @default 0
             */
            likes_count: number;
            /**
             * Is Liked By Me
             * @default false
             */
            is_liked_by_me: boolean;
            /** Id */
            id: number;
            /** Name */
            name: string;
            /** Cover Url */
            cover_url?: string | null;
            city: components["schemas"]["CityShort"];
            /** Rating Avg */
            readonly rating_avg: number | null;
        };
        /** VenueShort */
        VenueShort: {
            /** Id */
            id: number;
            /** Name */
            name: string;
            /** Cover Url */
            cover_url?: string | null;
            city: components["schemas"]["CityShort"];
        };
        /** VenueUpdate */
        VenueUpdate: {
            /** Name */
            name?: string | null;
            /** City Id */
            city_id?: number | null;
            /** Lat */
            lat?: number | null;
            /** Lng */
            lng?: number | null;
            /** Description */
            description?: string | null;
            /** Address */
            address?: string | null;
            /** Capacity */
            capacity?: number | null;
            /** Website */
            website?: string | null;
            /** Cover Url */
            cover_url?: string | null;
        };
        /** VersionOut */
        VersionOut: {
            /** Release Id */
            release_id: string;
        };
    };
    responses: never;
    parameters: never;
    requestBodies: never;
    headers: never;
    pathItems: never;
}
export type $defs = Record<string, never>;
export interface operations {
    liveness_api_v1_health_live_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HealthOut"];
                };
            };
        };
    };
    readiness_api_v1_health_ready_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ReadinessOut"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ReadinessOut"];
                };
            };
        };
    };
    version_api_v1_health_version_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["VersionOut"];
                };
            };
        };
    };
    register_api_v1_auth_register_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RegisterInput"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UserMe"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    login_api_v1_auth_login_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["LoginInput"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TokenPair"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    refresh_api_v1_auth_refresh_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RefreshInput"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TokenPair"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    logout_api_v1_auth_logout_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
        };
    };
    browser_login_api_v1_auth_browser_login_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["LoginInput"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BrowserToken"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    browser_refresh_api_v1_auth_browser_refresh_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BrowserToken"];
                };
            };
        };
    };
    browser_logout_api_v1_auth_browser_logout_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
        };
    };
    me_api_v1_me_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UserMe"];
                };
            };
        };
    };
    public_profile_api_v1_users__user_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                user_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UserOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_favorite_genres_api_v1_me_favorite_genres_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["GenreOut"][];
                };
            };
        };
    };
    put_favorite_genres_api_v1_me_favorite_genres_put: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["FavoriteGenresPut"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["GenreOut"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    my_artists_api_v1_me_artists_get: {
        parameters: {
            query?: {
                limit?: number;
                offset?: number;
                sort?: string;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Page_ArtistRatedShort_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    my_albums_api_v1_me_albums_get: {
        parameters: {
            query?: {
                limit?: number;
                offset?: number;
                sort?: string;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Page_AlbumRatedShort_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    my_tracks_api_v1_me_tracks_get: {
        parameters: {
            query?: {
                limit?: number;
                offset?: number;
                sort?: string;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Page_TrackRatedShort_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_artists_api_v1_artists_get: {
        parameters: {
            query?: {
                limit?: number;
                offset?: number;
                sort?: string;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Page_ArtistRatedShort_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_api_v1_artists_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ArtistCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ArtistOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    detail_api_v1_artists__artist_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                artist_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ArtistOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_api_v1_artists__artist_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                artist_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ArtistUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ArtistOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_albums_api_v1_albums_get: {
        parameters: {
            query?: {
                limit?: number;
                offset?: number;
                sort?: string;
                artist_id?: number | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Page_AlbumRatedShort_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_api_v1_albums_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AlbumCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AlbumOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    detail_api_v1_albums__album_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                album_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AlbumOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_api_v1_albums__album_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                album_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AlbumUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AlbumOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_tracks_api_v1_tracks_get: {
        parameters: {
            query?: {
                limit?: number;
                offset?: number;
                sort?: string;
                artist_id?: number | null;
                album_id?: number | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Page_TrackRatedShort_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_api_v1_tracks_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["TrackCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TrackOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    detail_api_v1_tracks__track_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                track_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TrackOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_api_v1_tracks__track_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                track_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["TrackUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TrackOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_public_genres_api_v1_genres_get: {
        parameters: {
            query?: {
                limit?: number;
                offset?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Page_GenreOut_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_api_v1_genres_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["GenreCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["GenreOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    put_api_v1_ratings_put: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RatingPut"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RatingResult"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_api_v1_ratings__target_type___target_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                target_type: components["schemas"]["RatingTarget"];
                target_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RatingResult"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    cities_api_v1_cities_get: {
        parameters: {
            query?: {
                limit?: number;
                offset?: number;
                q?: string | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Page_CityOut_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_api_v1_cities_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CityCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CityOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    venues_api_v1_venues_get: {
        parameters: {
            query?: {
                limit?: number;
                offset?: number;
                sort?: string;
                city_id?: number | null;
                min_lat?: number | null;
                max_lat?: number | null;
                min_lng?: number | null;
                max_lng?: number | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Page_VenueRatedShort_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_api_v1_venues_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["VenueCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["VenueOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    detail_api_v1_venues__venue_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                venue_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["VenueOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_api_v1_venues__venue_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                venue_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["VenueUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["VenueOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    types_api_v1_event_types_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["EventType"][];
                };
            };
        };
    };
    events_api_v1_events_get: {
        parameters: {
            query?: {
                limit?: number;
                offset?: number;
                sort?: string;
                city_id?: number | null;
                min_lat?: number | null;
                max_lat?: number | null;
                min_lng?: number | null;
                max_lng?: number | null;
                starts_after?: string | null;
                starts_before?: string | null;
                type_event_id?: number | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Page_EventOut_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_api_v1_events_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["EventCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["EventOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    detail_api_v1_events__event_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                event_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["EventOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    remove_api_v1_events__event_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                event_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_api_v1_events__event_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                event_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["EventUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["EventOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    listing_api_v1_reviews_get: {
        parameters: {
            query?: {
                limit?: number;
                offset?: number;
                target_type?: components["schemas"]["RatingTarget"] | null;
                target_id?: number | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Page_ReviewOut_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_api_v1_reviews_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ReviewCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ReviewOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    detail_api_v1_reviews__review_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                review_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ReviewOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_api_v1_reviews__review_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                review_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_api_v1_reviews__review_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                review_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ReviewUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ReviewOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    listing_api_v1_playlists_get: {
        parameters: {
            query?: {
                limit?: number;
                offset?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Page_PlaylistShort_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_api_v1_playlists_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PlaylistCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PlaylistOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    own_api_v1_me_playlists_get: {
        parameters: {
            query?: {
                limit?: number;
                offset?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Page_PlaylistShort_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    saved_api_v1_me_saved_playlists_get: {
        parameters: {
            query?: {
                limit?: number;
                offset?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Page_PlaylistShort_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    detail_api_v1_playlists__playlist_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                playlist_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PlaylistOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_api_v1_playlists__playlist_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                playlist_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_api_v1_playlists__playlist_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                playlist_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PlaylistUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PlaylistOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    tracks_api_v1_playlists__playlist_id__tracks_get: {
        parameters: {
            query?: {
                limit?: number;
                offset?: number;
            };
            header?: never;
            path: {
                playlist_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Page_PlaylistTrackItem_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    add_track_api_v1_playlists__playlist_id__tracks_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                playlist_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PlaylistTrackAdd"];
            };
        };
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    remove_track_api_v1_playlists__playlist_id__tracks__track_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                playlist_id: number;
                track_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    reorder_api_v1_playlists__playlist_id__tracks_order_put: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                playlist_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PlaylistReorder"];
            };
        };
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    put_api_v1_favorites_put: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["FavoriteCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["FavoriteRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    put_api_v1_favorites_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["FavoriteCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["FavoriteRead"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    remove_api_v1_favorites__entity_type___entity_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                entity_type: components["schemas"]["FavoriteTarget"];
                entity_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    listing_api_v1_me_favorites_get: {
        parameters: {
            query?: {
                limit?: number;
                offset?: number;
                entity_type?: components["schemas"]["FavoriteTarget"] | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Page_FavoriteRead_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    put_api_v1_follows_put: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["FollowCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["FollowOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    remove_api_v1_follows__target_type___target_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                target_type: components["schemas"]["FollowTarget"];
                target_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    listing_api_v1_me_following_get: {
        parameters: {
            query?: {
                limit?: number;
                offset?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Page_FollowOut_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    feed_api_v1_me_feed_get: {
        parameters: {
            query?: {
                limit?: number;
                offset?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Page_ActivityOut_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    image_upload_api_v1_media_images_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "multipart/form-data": components["schemas"]["Body_image_upload_api_v1_media_images_post"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MediaOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    audio_upload_api_v1_media_audio_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "multipart/form-data": components["schemas"]["Body_audio_upload_api_v1_media_audio_post"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MediaOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    metadata_api_v1_media__media_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                media_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MediaOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    content_api_v1_media__media_id__content_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                media_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    image_attach_api_v1_images__target_type___target_id__put: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                target_type: "user" | "artist" | "album" | "track" | "venue" | "playlist";
                target_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["MediaAttach"];
            };
        };
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    track_audio_api_v1_tracks__track_id__audio_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                track_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    audio_attach_api_v1_tracks__track_id__audio_put: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                track_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["MediaAttach"];
            };
        };
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    track_playback_api_v1_tracks__track_id__playback_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                track_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PlaybackOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    tracks_api_v1_recommendations_tracks_get: {
        parameters: {
            query?: {
                limit?: number;
                offset?: number;
                playable_only?: boolean;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RecommendationPage"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
}
