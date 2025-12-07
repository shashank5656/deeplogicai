from datetime import datetime
import re


DATE_FORMATS = [
    "%Y-%m-%d",
    "%d.%m.%Y",
    "%d/%m/%Y",
    "%d-%m-%Y",
]

def parse_date(value):
    """
    Parse a date string into a Python date object.
    Returns None if not parseable.
    """
    if not value:
        return None

    value = str(value).strip()

    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date()
        except:
            pass

    
    return None




def parse_amount(value):
    """
    Convert value into float.
    Handles:
        - '1,200.50'
        - '₹1200'
        - '$80'
        - '1200'
    Returns float or None.
    """
    if value is None:
        return None


    if isinstance(value, (int, float)):
        return float(value)


    s = str(value)

    s = re.sub(r"[^\d.\-,]", "", s)

    s = s.replace(",", "")

    s = s.strip()
    if s == "":
        return None

    try:
        return float(s)
    except:
        return None




def normalize_text(s):
    """
    Normalize text for comparison:
        - lowercase
        - trim spaces
    """
    if s is None:
        return ""
    return " ".join(str(s).strip().lower().split())
