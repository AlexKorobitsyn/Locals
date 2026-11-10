from fastapi import APIRouter

from APP.API.health import router as health_router
from APP.API.v1.admin import router as admin_router
from APP.API.v1.album import router as album_router
from APP.API.v1.artist import router as artist_router
from APP.API.v1.auth import router as auth_router
from APP.API.v1.city import router as city_router
from APP.API.v1.contribution import router as contribution_router
from APP.API.v1.event_log import router as event_log_router
from APP.API.v1.events import router as events_router
from APP.API.v1.experience import router as experience_router
from APP.API.v1.favorite import router as favorite_router
from APP.API.v1.follow import router as follow_router
from APP.API.v1.genre import router as genre_router
from APP.API.v1.geocoding import router as geocoding_router
from APP.API.v1.media import router as media_router
from APP.API.v1.playlist import router as playlist_router
from APP.API.v1.rating import router as rating_router
from APP.API.v1.recommendation import router as recommendation_router
from APP.API.v1.review import router as review_router
from APP.API.v1.studio import router as studio_router
from APP.API.v1.tracks import router as track_router
from APP.API.v1.user import router as user_router
from APP.API.v1.venue import router as venue_router

router = APIRouter(prefix="/api/v1")
router.include_router(health_router)
router.include_router(admin_router)
router.include_router(experience_router)
router.include_router(contribution_router)
router.include_router(auth_router)
router.include_router(user_router)
router.include_router(studio_router)
router.include_router(artist_router)
router.include_router(album_router)
router.include_router(track_router)
router.include_router(genre_router)
router.include_router(rating_router)

router.include_router(city_router)
router.include_router(geocoding_router)
router.include_router(venue_router)
router.include_router(events_router)
router.include_router(review_router)
router.include_router(playlist_router)
router.include_router(favorite_router)
router.include_router(follow_router)
router.include_router(event_log_router)

router.include_router(media_router)

router.include_router(recommendation_router)
