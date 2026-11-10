from fastapi import APIRouter, Response

from APP.core.config import SettingsDependency
from APP.core.db import SessionDependency
from APP.core.dependencies import CurrentUserDependency
from APP.schemas.common import Latitude, Longitude
from APP.schemas.geocoding import ReverseAddress
from APP.services.geocoding import reverse_address

router = APIRouter(prefix="/geocoding", tags=["geocoding"])


@router.get("/reverse", response_model=ReverseAddress)
async def reverse(
    lat: Latitude,
    lng: Longitude,
    user: CurrentUserDependency,
    session: SessionDependency,
    settings: SettingsDependency,
    response: Response,
):
    response.headers["Cache-Control"] = "no-store"
    return await reverse_address(session, settings, lat, lng)
