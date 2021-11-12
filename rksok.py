from enum import Enum
from abc import ABC, abstractmethod
import asyncio
import aiofiles.os as aiof
import aiofiles
import re
import inspect
import os


class RequestDoesNotMeetTheStandart(Exception):
    pass


class DataStorageInterface(ABC):
    @abstractmethod
    def get_data(self, name: str):
        pass

    @abstractmethod
    def delete_data(self, name: str):
        pass

    @abstractmethod
    def post_data(self, name: str, information: str):
        pass


class SQliteStorage(DataStorageInterface):
    def __init__(self):
        pass

    async def get_data(self, name: str):
        print("Получить данные человека по имени:", name)
        return f"{ResponseStatus.OK.value} {POSTFIX}"

    async def delete_data(self, name: str):
        print("Удалить данные человека по имени:", name)
        return f"{ResponseStatus.OK.value} {POSTFIX}"

    async def post_data(self, name: str, information: str):
        print(f"Изменить данные человека по имени: {name}")
        print(f"Изменить {information}")
        return f"{ResponseStatus.OK.value} {POSTFIX}"


class LocalDirectoryStorage(DataStorageInterface):

    HOME_DIR = "phonebook"
    FILE_PATH = HOME_DIR + "/{}.txt"


    def __init__(self):
        self.check_dir_exists()

    def check_dir_exists(self) -> None:
        if not os.path.exists(os.path.join(os.getcwd(),LocalDirectoryStorage.HOME_DIR)):
            os.mkdir(LocalDirectoryStorage.HOME_DIR)

    async def get_data(self, name: str):
        file_name = LocalDirectoryStorage.FILE_PATH.format(name)
        if not aiof.os.path.exists(file_name):
            return f"{ResponseStatus.NOTFOUND.value} {POSTFIX}"
        async with aiofiles.open(file_name, mode="r") as f:
            content = await f.read()
        return f"{ResponseStatus.OK.value} {POSTFIX} {content}"

    async def delete_data(self, name: str):
        file_name = LocalDirectoryStorage.FILE_PATH.format(name)
        if not aiof.os.path.exists(file_name):
            return f"{ResponseStatus.NOTFOUND.value} {POSTFIX}"
        await aiof.remove(file_name)
        return f"{ResponseStatus.OK.value} {POSTFIX}"

    async def post_data(self, name: str, information: str):
        file_name = LocalDirectoryStorage.FILE_PATH.format(name)
        async with aiofiles.open(file_name, mode="w") as f:
            await f.write(information)
            await f.flush()
        return f"{ResponseStatus.OK.value} {POSTFIX}"


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


VERB_TO_FUNCTION = {
    RequestVerb.GET: "get_data",
    RequestVerb.WRITE: "post_data",
    RequestVerb.DELETE: "delete_data",
}

PREFIX = "АМОЖНА? РКСОК/1.0\r\n"
POSTFIX = "РКСОК/1.0\r\n\r\n"
ENCODING = "UTF-8"
MESSAGE_PATTERN = r"(.*?)\s(.*)\w{5}.*\s(.*)[.\r\n]*"


storage = LocalDirectoryStorage()


async def check_message(message):
    reader, writer = await asyncio.open_connection("vragi-vezde.to.digital", 51624)
    writer.write(message.encode(ENCODING))
    data = await reader.read(1024)
    writer.close()
    return data


async def data_handling(verb, *args):
    if not hasattr(storage, VERB_TO_FUNCTION.get(verb)) or args[0].isspace():
        raise RequestDoesNotMeetTheStandart
    function = getattr(storage, VERB_TO_FUNCTION.get(verb))
    return await function(*args[: len(inspect.signature(function).parameters.keys())])


def parce_response(data):
    return re.sub(MESSAGE_PATTERN, r"\1|\2|\3", data, count=1).split("|")


async def data_manipulations(raw_data):

    data = raw_data.decode(ENCODING)
    command, name_field, information = parce_response(data)
    if len(name_field) > 30:
        return f"{ResponseStatus.INCORRECT_REQUEST.value} {POSTFIX}"

    message = PREFIX + data
    server_response = await check_message(message)

    if server_response.decode(ENCODING).startswith(
        f"{RegulatoryServerResponseStatus.APPROVED.value} "
    ):
        for verb in RequestVerb:
            if command.startswith(verb.value):
                break
        storage_response = await asyncio.gather(
            data_handling(verb, name_field, information), return_exceptions=True
        )
        print(storage_response)
        response = storage_response[0]
        if isinstance(response, Exception):
            response = f"{ResponseStatus.INCORRECT_REQUEST.value} {POSTFIX}"
        return response


async def handle_echo(reader, writer):
    try:
        raw_data = await asyncio.wait_for(reader.readuntil(separator=b"\r\n\r\n"), 10)
    except asyncio.IncompleteReadError as e:
        raw_data = e.partial

    response = await data_manipulations(raw_data)

    writer.write(response.encode(ENCODING))
    await writer.drain()
    writer.close()


async def main():
    server = await asyncio.start_server(handle_echo, "127.0.0.1", 8888)

    addrs = ", ".join(str(sock.getsockname()) for sock in server.sockets)
    print(f"Serving on {addrs}")

    async with server:
        await server.serve_forever()


asyncio.run(main(), debug=True)
