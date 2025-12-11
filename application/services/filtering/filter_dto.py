from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, validator

from application.common.utils import DATE_FMT


class NotesFilter(BaseModel):
    title: Optional[str] = None
    tag: Optional[str] = None

    date_eq: Optional[date] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None

    @validator("date_eq", "date_from", "date_to", pre=True)
    def _coerce_date(cls, value):
        if value is None or isinstance(value, date):
            return value
        if isinstance(value, str) and value.strip():
            try:
                return datetime.strptime(value.strip(), DATE_FMT).date()
            except Exception:
                raise ValueError(f"Invalid date format. Expected {DATE_FMT}")
        return None

    class Config:
        str_strip_whitespace = True
        validate_assignment = True
