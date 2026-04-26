from fastapi import APIRouter, Depends
from sqlmodel import Session

from smart_irrigation_system.server.configuration.schemas.global_config import (
    GlobalConfigRead,
    GlobalConfigUpdate,
)
from smart_irrigation_system.server.configuration.services.global_config_service import GlobalConfigService
from smart_irrigation_system.server.db.session import get_session


router = APIRouter()


@router.get(
    "/",
    summary="Get global configuration",
    response_model=GlobalConfigRead,
    status_code=200,
)
def get_global_config(session: Session = Depends(get_session)):
    service = GlobalConfigService(session)
    config = service.get_or_create()
    return GlobalConfigRead.model_validate(config)


@router.patch(
    "/",
    summary="Update global configuration",
    response_model=GlobalConfigRead,
    status_code=200,
)
def update_global_config(data: GlobalConfigUpdate, session: Session = Depends(get_session)):
    service = GlobalConfigService(session)
    config = service.update(data)
    return GlobalConfigRead.model_validate(config)
