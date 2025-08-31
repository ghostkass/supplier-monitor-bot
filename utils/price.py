\
import re
from typing import Optional

# Robust price parsing for common formats, including "2 000 F CFA", "2.000,50 €", "$1,999.00"
def parse_price(text: str) -> Optional[float]:
    if not text:
        return None
    t = text.strip()

    # Replace non-breaking spaces and thin spaces
    t = t.replace('\xa0', ' ').replace('\u202f', ' ')
    # Remove currency symbols/words but keep separators
    t = re.sub(r'(F\s?CFA|FCFA|CFA|€|\$|USD|EUR|XOF|XAF|£)', '', t, flags=re.IGNORECASE)

    # Normalize decimal separators:
    # - If both ',' and '.' exist, assume European style "1.234,56" -> remove thousands '.' keep comma as decimal
    if ',' in t and '.' in t:
        # remove thousands separators '.'
        t = re.sub(r'\.(?=\d{3}(\D|$))', '', t)
        # replace comma with dot for decimal
        t = t.replace(',', '.')
    else:
        # If only commas present, they might be thousands OR decimal; try to detect decimal by last occurrence
        if ',' in t:
            # If pattern ends with ",dd"
            if re.search(r',\d{1,2}\D*$', t):
                t = t.replace(',', '.')
            else:
                t = t.replace(',', '')
        # If only dots present, likely thousands or decimal; remove thousands dots (groups of 3)
        if '.' in t:
            t = re.sub(r'\.(?=\d{3}(\D|$))', '', t)

    # Remove spaces
    t = re.sub(r'\s+', '', t)

    # Extract first float-like number
    m = re.search(r'([0-9]+(?:\.[0-9]+)?)', t)
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:
        return None
