import os
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from uuid import UUID

from presentation import dependencies as deps

from application.services.exporting.export_dto import NotesExport

from application.use_cases.notes.export_note import ExportNoteUseCase


router = APIRouter(prefix="/export", tags=["exporting"], dependencies=[Depends(deps.get_hardcoded_auth)])



@router.get("/export/{note_id}")
async def export_note_endpoint(
    note_id: int,
    user_uuid: UUID = Depends(deps.get_current_user_uuid),
    export_note_use_case: ExportNoteUseCase = Depends(deps.get_export_note_use_case),
):
    """Eksportuje notatkę do pliku tekstowego.
    
    - Odszyfrowuje tytuł i zawartość notatki
    - Tworzy plik .txt o nazwie równej tytułowi notatki
    - Zawartość pliku to odszyfrowana treść notatki
    - Zwraca plik do pobrania
    """
    try:
        export_request = NotesExport(note_id=note_id, user_uuid=user_uuid)
        file_path, filename = await export_note_use_case.execute(export_request)

        if not os.path.exists(file_path):
            raise HTTPException(status_code=500, detail="Nie udało się utworzyć pliku")

        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd podczas eksportu: {str(e)}")