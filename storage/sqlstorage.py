import databases
import sqlalchemy

from typing import NamedTuple
from dataclasses import dataclass

from resources import strings
from storage.repositories import DataStorageInterface



@dataclass
class SQLStorage(DataStorageInterface):  # , aobject):
    """SQlite storage."""

    DATABASE_URL: str = "sqlite:///./rksok.db"

    def not_found_handler(func):
        async def inner(*args, **kwars):
            try:
                return await func(*args, **kwars)
            except TypeError:
                return strings.NOTFOUND
        return inner

    def __init__(self):
        self.database = databases.Database(self.DATABASE_URL)
        self.metadata = sqlalchemy.MetaData()
        self.phonebook = sqlalchemy.Table(
            "phonebook",
            self.metadata,
            sqlalchemy.Column("name", sqlalchemy.String, primary_key=True),
            sqlalchemy.Column("phone", sqlalchemy.String),
        )
        self.engine = sqlalchemy.create_engine(
            self.DATABASE_URL, connect_args={"check_same_thread": False}
        )
        self.metadata.create_all(self.engine)

    @not_found_handler
    async def get_data(self, message: NamedTuple):
        async with databases.Database(self.DATABASE_URL) as db:
            content = await db.fetch_one(
                "select phone from phonebook where name = :name",
                values={"name": message.name_field},
            )
            return strings.CORRECT.format(data=content[0])

    @not_found_handler
    async def delete_data(self, message: NamedTuple):
        async with databases.Database(self.DATABASE_URL) as db:
            await db.execute(
                "delete from phonebook where name = :name",
                values={"name": message.name_field},
            )
            return strings.DONE

    @not_found_handler
    async def post_data(self, message: NamedTuple):
        async with databases.Database(self.DATABASE_URL) as db:
            values = {"name": message.name_field, "phone": message.information}
            await db.execute(
                "insert or ignore into phonebook values (:name,:phone)",
                values=values,
            )
            await db.execute(
                "update phonebook set phone = :phone where name = :name",
                values=values,
            )
            return strings.DONE
