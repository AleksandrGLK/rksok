from enum import Enum

class RequestVerb(Enum):
    """Verbs specified in RKSOK specs for requests"""

    GET = "ОТДОВАЙ"
    DELETE = "УДОЛИ"
    WRITE = "ЗОПИШИ"


class ResponseStatus(Enum):
    """Response statuses specified in RKSOK specs for responses"""

    OK = "НОРМАЛДЫКС"
    NOTFOUND = "НИНАШОЛ"
    INCORRECT_REQUEST = "НИПОНЯЛ"


class RegulatoryServerResponseStatus(Enum):
    APPROVED = "МОЖНА"
    NOT_APPROVED = "НИЛЬЗЯ"
