
from fastapi import APIRouter,  Depends
from uuid import UUID

from presentation import dependencies as deps

from application.services.self_delete_x_time import DeleteXTime


router = APIRouter(prefix="/time_perma", tags=["time"], dependencies=[Depends(deps.get_hardcoded_auth)])


@router.delete("/time_perma", response_model=dict)
async def auto_delete(
    user_uuid: UUID = Depends(deps.get_current_user_uuid),
    self_delete_service: DeleteXTime = Depends(deps.get_self_delete_service),
):
    """Automatyczne usuwanie notatek z kosza po przekroczeniu czasu TTL.
    
    - Sprawdza wszystkie notatki w koszu
    - Usuwa na stałe te, które przekroczyły czas życia (TTL)
    - Zwraca liczbę usuniętych notatek
    """
    deleted_count = await self_delete_service.execute_all(user_uuid=user_uuid)
    return {
        "message": f"Automatycznie usunięto {deleted_count} notatek z kosza",
        "deleted_count": deleted_count
    }
