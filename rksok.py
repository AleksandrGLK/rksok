import asyncio
import re
import inspect

from resources import strings

from storage.repositories import (
    DataStorageInterface,
    SQliteStorage,
    LocalDirectoryStorage,
)
from errors.validation_error import RequestDoesNotMeetTheStandart
from resources.conditions import (
    RequestVerb,
    RegulatoryServerResponseStatus,
)


VERB_TO_FUNCTION = {
    RequestVerb.GET: "get_data",
    RequestVerb.WRITE: "post_data",
    RequestVerb.DELETE: "delete_data",
}


ENCODING = "UTF-8"

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
    return re.sub(strings.MESSAGE_PATTERN, r"\1|\2|\3", data, count=1).split("|")


async def data_manipulations(raw_data):

    data = raw_data.decode(ENCODING)
    command, name_field, information = parce_response(data)
    if len(name_field) > 30:
        return strings.INCORRECT_REQUEST

    message = strings.PREFIX + data
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
        response = storage_response[0]
        if isinstance(response, Exception):
            response = strings.INCORRECT_REQUEST
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
