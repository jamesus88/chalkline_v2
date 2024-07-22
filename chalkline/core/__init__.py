from datetime import datetime
from pytz import timezone

TIMEZONE = timezone('US/Eastern')

def now():
    return datetime.now(TIMEZONE)

def localize(dt: datetime):
    return dt.astimezone(TIMEZONE)

def check_unique(cls, field, value):
    if cls.col.count_documents({field: value}) > 0:
        raise ValueError(f"{field} is already taken! Try another one.")
    else:
        return value