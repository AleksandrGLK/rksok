#!/usr/bin/python3

import asyncio
import re
import sys

from collections import namedtuple
from typing import NamedTuple

from resources import strings
from core import config
from core.logging import logger
from storage.repositories import STORAGE_FACTORY
from errors.validation_error import RequestDoesNotMeetTheStandart, EmptyNameField
from resources.conditions import (
    RequestVerb,
    RegulatoryServerResponseStatus,
    VERB_TO_FUNCTION,
)


Message = namedtuple("Message", "command name_field information verb")


class RKSOK:
    """RKSOK server. More than yellow pages."""

    def __init__(self, storage):
        self.storage = STORAGE_FACTORY[storage]

    @staticmethod
    async def check_message(data: bytes) -> str:
        logger.info("Connecting to {} port {}".format(*config.PERMISSION_SERVER))
        """Sends sequest to verify the possibility of processing client requests."""
        reader, writer = await asyncio.open_connection(*config.PERMISSION_SERVER)
        message = strings.PREFIX + data
        writer.write(message.encode(config.ENCODING))
        data = await reader.read(1024)
        writer.close()
        return data.decode(config.ENCODING)

    async def data_handling(self, message: NamedTuple):
        """Sends a request to the repository depending on the client command."""
        if not hasattr(self.storage, VERB_TO_FUNCTION.get(message.verb)):
            raise RequestDoesNotMeetTheStandart
        function = getattr(self.storage, VERB_TO_FUNCTION.get(message.verb))
        return await function(message)

    @staticmethod
    def parse_client_request(data: str) -> NamedTuple:
        """Parsing the client's message into meaningful parts."""
        try:
            command, name_field, information = re.sub(
                config.MESSAGE_PATTERN, r"\1|\2|\3", data, count=1
            ).split("|")

            for verb in RequestVerb:
                if command == verb.value:
                    break
            else:
                logger.exception("Can't parse client message")
                raise RequestDoesNotMeetTheStandart
            RKSOK.name_validation(name_field)
            logger.info(
                "Message parsed and validated \n command:{} name:{} info:{} verb:{}".format(
                    command, name_field, information, verb
                )
            )
            return Message(command, name_field, information, verb)
        except ValueError:
            logger.exception("Can't parse client message")
            raise RequestDoesNotMeetTheStandart

    @staticmethod
    def name_validation(name: str) -> None:
        """Client name size validation."""
        logger.info("Name validation")
        if not name or name.isspace():
            logger.exception("Failed name is empty: Name validation")
            raise EmptyNameField
        elif len(name) > 30:
            logger.exception("Failed by length: Name validation")
            raise RequestDoesNotMeetTheStandart

    async def parse_server_response(
        self, server_response: str, message: NamedTuple
    ) -> str:
        """Message processing from the check server."""
        logger.info("Parsing server response")
        if not server_response.startswith(
            f"{RegulatoryServerResponseStatus.APPROVED.value} "
        ):
            logger.info("Permisson Denied by regulatory service")
            return server_response
        logger.info("Data handling request")
        storage_response = await asyncio.gather(
            self.data_handling(message),
            return_exceptions=True,
        )
        response = storage_response[0]
        logger.info("Return result: %s", response)
        if isinstance(response, Exception):
            response = strings.INCORRECT_REQUEST
        return response

    async def client_message_processing(self, client_message: str) -> str:
        """Client message processing."""
        message = RKSOK.parse_client_request(client_message)
        server_response = await RKSOK.check_message(client_message)
        return (server_response, message)

    async def read_message(self, reader) -> str:
        """Reading message from client."""
        message = b""
        while True:
            try:
                data = await asyncio.wait_for(reader.read(1024), timeout=10)
            except asyncio.exceptions.TimeoutError:
                raise RequestDoesNotMeetTheStandart
            message += data
            if message.endswith(b"\r\n\r\n"):
                break
        return message.decode(config.ENCODING)

    async def rksok_server(self, reader, writer) -> None:
        """RKSOK server function."""
        try:
            logger.info("Waiting for message")
            client_message = await self.read_message(reader)
            logger.info("Received message %s", client_message)
            logger.info("Processing message ...")
            server_response, message = await self.client_message_processing(
                client_message
            )
            response = await self.parse_server_response(server_response, message)
        except RequestDoesNotMeetTheStandart as e:
            response = strings.INCORRECT_REQUEST
        except EmptyNameField as e:
            response = strings.NOTFOUND

        writer.write(response.encode(config.ENCODING))
        await writer.drain()
        writer.close()

    async def __call__(self) -> None:
        logger.info("Connecting to {} port {}".format(*config.SERVER_ADDRESS))
        server = await asyncio.start_server(self.rksok_server, *config.SERVER_ADDRESS)
        addrs = ", ".join(str(sock.getsockname()) for sock in server.sockets)
        print(f"Serving on {addrs}")
        async with server:
            await server.serve_forever()


if __name__ == "__main__":
    rksok = RKSOK("sqlite")
    asyncio.run(rksok(), debug=True)
