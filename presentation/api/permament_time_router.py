
from fastapi import APIRouter,  Depends

from presentation import dependencies as deps

from application.services.self_delete_x_time import Delete_X_Time


router = APIRouter(prefix="/time_perma", tags=["time"], dependencies=[Depends(deps.get_hardcoded_auth)])


@router.delete("/time_perma", response_model=dict)
async def auto_delete(
    self_delete_service: Delete_X_Time = Depends(deps.get_self_delete_service),
):
    """Automatyczne usuwanie notatek z kosza po przekroczeniu czasu TTL.
    
    - Sprawdza wszystkie notatki w koszu
    - Usuwa na stałe te, które przekroczyły czas życia (TTL)
    - Zwraca liczbę usuniętych notatek
    """
    deleted_count = await self_delete_service.execute_all()
    return {
        "message": f"Automatycznie usunięto {deleted_count} notatek z kosza",
        "deleted_count": deleted_count
    }
