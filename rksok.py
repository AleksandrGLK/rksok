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
    async def check_message(data: bytes) -> str:
        reader, writer = await asyncio.open_connection("vragi-vezde.to.digital", 51624)
        message = strings.PREFIX + data
        writer.write(message.encode(ENCODING))
        data = await reader.read(1024)
        writer.close()
        return data.decode(ENCODING)

    async def data_handling(self, verb, *args):
        if not hasattr(
            self.storage, VERB_TO_FUNCTION.get(verb)
        ):  # or args[0].isspace():
            raise RequestDoesNotMeetTheStandart
        function = getattr(self.storage, VERB_TO_FUNCTION.get(verb))
        return await function(
            *args[: len(inspect.signature(function).parameters.keys())]
        )

    @staticmethod
    def parce_response(data: str) -> list:
        try:
            command, name_field, information = re.sub(
                strings.MESSAGE_PATTERN, r"\1|\2|\3", data, count=1
            ).split("|")

            for verb in RequestVerb:
                if command == verb.value:
                    break
            else:
                raise RequestDoesNotMeetTheStandart

            if len(name_field) > 30:
                raise RequestDoesNotMeetTheStandart
            return (command, name_field, information)
        except ValueError:
            raise RequestDoesNotMeetTheStandart

    async def data_manipulations(self, raw_data: bytes) -> str:

        data = raw_data.decode(ENCODING)
        command, name_field, information = RKSOK.parce_response(data)

        if not name_field:
            return strings.NOTFOUND

        server_response = await RKSOK.check_message(data)

        if not server_response.startswith(
            f"{RegulatoryServerResponseStatus.APPROVED.value} "
        ):
            return server_response
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
            try:
                data = await asyncio.wait_for(reader.read(1024), timeout=10)
            except asyncio.exceptions.TimeoutError:
                raise RequestDoesNotMeetTheStandart
            message += data
            if message.endswith(b"\r\n\r\n"):
                break
        return message

    async def handle_echo(self, reader, writer) -> None:
        try:
            raw_data = await self.read_message(reader)
            response = await self.data_manipulations(raw_data)
        except RequestDoesNotMeetTheStandart as e:
            response = strings.INCORRECT_REQUEST

        writer.write(response.encode(ENCODING))
        await writer.drain()
        writer.close()

    async def __call__(self) -> None:
        server = await asyncio.start_server(self.handle_echo, "127.0.0.1", 7777)

        addrs = ", ".join(str(sock.getsockname()) for sock in server.sockets)
        print(f"Serving on {addrs}")

        async with server:
            await server.serve_forever()


rksok = RKSOK()
asyncio.run(rksok(), debug=True)
