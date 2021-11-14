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
    """Response statuses from the check server."""

    APPROVED = "МОЖНА"
    NOT_APPROVED = "НИЛЬЗЯ"



VERB_TO_FUNCTION = {
    RequestVerb.GET: "get_data",
    RequestVerb.WRITE: "post_data",
    RequestVerb.DELETE: "delete_data",
}
