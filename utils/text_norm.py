import re
from typing import Optional

def normalize_text(text: Optional[str]) -> str:
    if not text:
        return ""
    # collapse whitespace / lowercase for keyword search
    t = re.sub(r'\s+', ' ', text).strip().lower()
    return t
