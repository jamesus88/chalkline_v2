from datetime import datetime
from pytz import timezone
from bson import ObjectId

TIMEZONE = timezone('US/Eastern')

def now():
    dt = datetime.now(TIMEZONE).replace(tzinfo=None)
    return dt

def localize(dt: datetime):
    return dt.astimezone(TIMEZONE)

def check_unique(cls, field: str, value):
    if cls.col.count_documents({field: value}) > 0:
        raise ValueError(f"{field.title()} is already taken! Try another one.")
    else:
        return value

def _safe(obj):
    obj['_id'] = str(obj['_id'])
    return obj

def remove_dups(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]

def get_us_states():
    return {
        # https://en.wikipedia.org/wiki/List_of_states_and_territories_of_the_United_States#States.
        "AK": "Alaska",
        "AL": "Alabama",
        "AR": "Arkansas",
        "AZ": "Arizona",
        "CA": "California",
        "CO": "Colorado",
        "CT": "Connecticut",
        "DE": "Delaware",
        "FL": "Florida",
        "GA": "Georgia",
        "HI": "Hawaii",
        "IA": "Iowa",
        "ID": "Idaho",
        "IL": "Illinois",
        "IN": "Indiana",
        "KS": "Kansas",
        "KY": "Kentucky",
        "LA": "Louisiana",
        "MA": "Massachusetts",
        "MD": "Maryland",
        "ME": "Maine",
        "MI": "Michigan",
        "MN": "Minnesota",
        "MO": "Missouri",
        "MS": "Mississippi",
        "MT": "Montana",
        "NC": "North Carolina",
        "ND": "North Dakota",
        "NE": "Nebraska",
        "NH": "New Hampshire",
        "NJ": "New Jersey",
        "NM": "New Mexico",
        "NV": "Nevada",
        "NY": "New York",
        "OH": "Ohio",
        "OK": "Oklahoma",
        "OR": "Oregon",
        "PA": "Pennsylvania",
        "RI": "Rhode Island",
        "SC": "South Carolina",
        "SD": "South Dakota",
        "TN": "Tennessee",
        "TX": "Texas",
        "UT": "Utah",
        "VA": "Virginia",
        "VT": "Vermont",
        "WA": "Washington",
        "WI": "Wisconsin",
        "WV": "West Virginia",
        "WY": "Wyoming",
        # https://en.wikipedia.org/wiki/List_of_states_and_territories_of_the_United_States#Federal_district.
        "DC": "District of Columbia",
        # https://en.wikipedia.org/wiki/List_of_states_and_territories_of_the_United_States#Inhabited_territories.
        "AS": "American Samoa",
        "GU": "Guam GU",
        "MP": "Northern Mariana Islands",
        "PR": "Puerto Rico PR",
        "VI": "U.S. Virgin Islands",
    }