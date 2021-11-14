from resources.conditions import ResponseStatus

PROTOCOL = "РКСОК/1.0"
PREFIX = "АМОЖНА? РКСОК/1.0\r\n"
POSTFIX = "\r\n\r\n"

INCORRECT_REQUEST = f"{ResponseStatus.INCORRECT_REQUEST.value} {PROTOCOL}{POSTFIX}"
CORRECT = f"{ResponseStatus.OK.value} {PROTOCOL}\r\n" + "{data}" + f"{POSTFIX}"
DONE = f"{ResponseStatus.OK.value} {PROTOCOL}{POSTFIX}"
NOTFOUND = f"{ResponseStatus.NOTFOUND.value} {PROTOCOL}{POSTFIX}"
