import aiofiles.os as aiof
import aiofiles

import os
from typing import NamedTuple

from resources import strings
from dataclasses import dataclass
from storage.repositories import DataStorageInterface

@dataclass
class LocalDirectoryStorage(DataStorageInterface):
    """Local directory storage"""

    HOME_DIR : str = "phonebook"
    FILE_PATH : str = HOME_DIR + "/{}.txt"

    def __init__(self):
        self.check_dir_exists()

    def check_dir_exists(self) -> None:
        """Check if the local directory exists."""
        if not os.path.exists(os.path.join(os.getcwd(), self.HOME_DIR)):
            os.mkdir(self.HOME_DIR)

    async def get_data(self, message: NamedTuple):
        """Returns the contents of the file if there is one."""
        file_name = self.FILE_PATH.format(message.name_field)
        if not aiof.os.path.exists(file_name):
            return strings.NOTFOUND
        async with aiofiles.open(file_name, mode="r") as f:
            content = await f.read()
        return strings.CORRECT.format(data=content)

    async def delete_data(self, message: NamedTuple):
        """Delete the contents of the file if there is one."""
        file_name = self.FILE_PATH.format(message.name_field)
        if not aiof.os.path.exists(file_name):
            return strings.NOTFOUND
        await aiof.remove(file_name)
        return strings.DONE

    async def post_data(self, message: NamedTuple):
        """Change the contents of the file if there is one else make new one."""
        file_name = self.FILE_PATH.format(message.name_field)
        async with aiofiles.open(file_name, mode="w") as f:
            await f.write(message.information)
            await f.flush()
        return strings.DONE
