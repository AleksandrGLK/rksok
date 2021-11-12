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


class RKSOK:
    def __init__(self):
        self.storage = LocalDirectoryStorage()

    @staticmethod
    async def check_message(data: bytes) -> bytes:
        reader, writer = await asyncio.open_connection("vragi-vezde.to.digital", 51624)
        message = strings.PREFIX + data
        writer.write(message.encode(ENCODING))
        data = await reader.read(1024)
        writer.close()
        return data

    async def data_handling(self, verb, *args):
        if not hasattr(self.storage, VERB_TO_FUNCTION.get(verb)) or args[0].isspace():
            raise RequestDoesNotMeetTheStandart
        function = getattr(self.storage, VERB_TO_FUNCTION.get(verb))
        return await function(
            *args[: len(inspect.signature(function).parameters.keys())]
        )

    @staticmethod
    def parce_response(data: str) -> list:
        return re.sub(strings.MESSAGE_PATTERN, r"\1|\2|\3", data, count=1).split("|")

    async def data_manipulations(self, raw_data: bytes) -> str:

        data = raw_data.decode(ENCODING)
        command, name_field, information = RKSOK.parce_response(data)
        if len(name_field) > 30 :
            return strings.INCORRECT_REQUEST

        server_response = await RKSOK.check_message(data)

        if server_response.decode(ENCODING).startswith(
            f"{RegulatoryServerResponseStatus.APPROVED.value} "
        ):
            for verb in RequestVerb:
                if command.startswith(verb.value):
                    break
            storage_response = await asyncio.gather(
                self.data_handling(verb, name_field, information),
                return_exceptions=True,
            )
            response = storage_response[0]
            if isinstance(response, Exception):
                response = strings.INCORRECT_REQUEST
            return response

    async def read_message(self, reader):
        message = b""
        while True:
            data = await reader.read(1024)
            if not data:
                break
            message += data
        if not message.endswith(b'\r\n\r\n'):
            raise RequestDoesNotMeetTheStandart
        return message

    async def handle_echo(self, reader, writer) -> None:
        try:
            raw_data = await asyncio.wait_for(self.read_message(reader), timeout=10)
            response = await self.data_manipulations(raw_data)
        except (asyncio.exceptions.TimeoutError, RequestDoesNotMeetTheStandart) as e:
            response = strings.INCORRECT_REQUEST

        writer.write(response.encode(ENCODING))
        await writer.drain()
        writer.close()

    async def __call__(self) -> None:
        server = await asyncio.start_server(self.handle_echo, "127.0.0.1", 8888)

        addrs = ", ".join(str(sock.getsockname()) for sock in server.sockets)
        print(f"Serving on {addrs}")

        async with server:
            await server.serve_forever()


rksok = RKSOK()
asyncio.run(rksok(), debug=True)
