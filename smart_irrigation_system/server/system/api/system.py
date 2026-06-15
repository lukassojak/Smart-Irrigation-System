from fastapi import APIRouter
from smart_irrigation_system.__version__ import __version__

router = APIRouter()

@router.get(
    "/version",
    summary="Get server version",
    response_model=dict,
)
def get_version():
    try:
        return {"version": __version__}
    except Exception as e:
        return {"error": str(e)}