class RequestDoesNotMeetTheStandart(Exception):
    """Error that occurs when we cannot parse some strange response from client."""
    pass


class EmptyNameField(Exception):
    """Error that occurs when the name field in response is empty."""
    pass
