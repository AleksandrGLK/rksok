from typing import NamedTuple
from abc import ABC, abstractmethod
import sqlite3
import aiofiles.os as aiof
import aiofiles
import aiosqlite
import os
from resources import strings


class DataStorageInterface(ABC):
    """Simple data storage interface."""

    @abstractmethod
    def get_data(self, message: NamedTuple):
        pass

    @abstractmethod
    def delete_data(self, message: NamedTuple):
        pass

    @abstractmethod
    def post_data(self, message: NamedTuple):
        pass


class SQliteStorage(DataStorageInterface):  # , aobject):
    """SQlite storage."""

    def __init__(self):
        self.phonebook_db = "rksok.db"
        self.create()

    def create(self):
        with sqlite3.connect(self.phonebook_db) as db:
            db.execute(f"create table if not exists phonebook (name text, phone text)")
            db.commit()

    async def get_data(self, message: NamedTuple):
        try:
            async with aiosqlite.connect(self.phonebook_db) as db:
                async with db.execute(
                    "select phone from phonebook where name = '%s'", message.name_field
                ) as cursor:
                    data = await cursor.fetchone()
            return strings.CORRECT.format(data=content)
        except Exception as e:
            return strings.NOTFOUND

    async def delete_data(self, message: NamedTuple):
        try:
            async with aiosqlite.connect(self.phonebook_db) as db:
                await db.execute(
                    "delete from phonebook where name = '%s'",{message.name_field}
                )
            return strings.DONE
        except Exception as e:
            print(e)
            return strings.NOTFOUND

    async def post_data(self, message: NamedTuple):
        try:
            async with aiosqlite.connect(self.phonebook_db) as db:
                await db.execute(
                    f"insert or ignore into phonebook values (?,?)",
                    [message.name_field, message.information],
                )
                await db.execute(
                    f"update phonebook set phone = '{message.information}' where name = '{message.name_field}'"
                )
                await db.commit()
            return strings.DONE
        except Exception as e:
            print(e)
            return strings.NOTFOUND


class LocalDirectoryStorage(DataStorageInterface):
    """Local directory storage"""

    HOME_DIR = "phonebook"
    FILE_PATH = HOME_DIR + "/{}.txt"

    def __init__(self):
        self.check_dir_exists()

    def check_dir_exists(self) -> None:
        """Check if the local directory exists."""
        if not os.path.exists(
            os.path.join(os.getcwd(), LocalDirectoryStorage.HOME_DIR)
        ):
            os.mkdir(LocalDirectoryStorage.HOME_DIR)

    async def get_data(self, message: NamedTuple):
        """Returns the contents of the file if there is one."""
        file_name = LocalDirectoryStorage.FILE_PATH.format(message.name_field)
        if not aiof.os.path.exists(file_name):
            return strings.NOTFOUND
        async with aiofiles.open(file_name, mode="r") as f:
            content = await f.read()
        return strings.CORRECT.format(data=content)

    async def delete_data(self, message: NamedTuple):
        """Delete the contents of the file if there is one."""
        file_name = LocalDirectoryStorage.FILE_PATH.format(message.name_field)
        if not aiof.os.path.exists(file_name):
            return strings.NOTFOUND
        await aiof.remove(file_name)
        return strings.DONE

    async def post_data(self, message: NamedTuple):
        """Change the contents of the file if there is one else make new one."""
        file_name = LocalDirectoryStorage.FILE_PATH.format(message.name_field)
        async with aiofiles.open(file_name, mode="w") as f:
            await f.write(message.information)
            await f.flush()
        return strings.DONE


STORAGE_FACTORY = {
    "sqlite": SQliteStorage(),
    "local_files": LocalDirectoryStorage(),
}
