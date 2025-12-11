from datetime import datetime, date
from typing import Optional, List


DATE_FMT = "%d-%m-%y"



def parse_created_at_str(date_str: Optional[str]) -> Optional[date]:
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, DATE_FMT).date()
    except Exception:
        return None


def tags_to_list(tags: Optional[str]) -> List[str]:
    if not tags:
        return []

    raw = [
        p.strip()
        for part in tags.replace(";", ",").split(";")
        for p in part.split(",")
    ]

    output: List[str] = []
    for item in raw:
        if not item:
            continue
        output.extend([t for t in item.split() if t])

    return [t.lower() for t in output]
