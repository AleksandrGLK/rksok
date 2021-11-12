from abc import ABC, abstractmethod
import aiofiles.os as aiof
import aiofiles
import os
from resources import strings


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
        return strings.DONE

    async def delete_data(self, name: str):
        print("Удалить данные человека по имени:", name)
        return strings.DONE

    async def post_data(self, name: str, information: str):
        print(f"Изменить данные человека по имени: {name}")
        print(f"Изменить {information}")
        return strings.DONE


class LocalDirectoryStorage(DataStorageInterface):

    HOME_DIR = "phonebook"
    FILE_PATH = HOME_DIR + "/{}.txt"

    def __init__(self):
        self.check_dir_exists()

    def check_dir_exists(self) -> None:
        if not os.path.exists(
            os.path.join(os.getcwd(), LocalDirectoryStorage.HOME_DIR)
        ):
            os.mkdir(LocalDirectoryStorage.HOME_DIR)

    async def get_data(self, name: str):
        file_name = LocalDirectoryStorage.FILE_PATH.format(name)
        if not aiof.os.path.exists(file_name):
            return strings.NOTFOUND
        async with aiofiles.open(file_name, mode="r") as f:
            content = await f.read()
        return strings.CORRECT.format(data=content)

    async def delete_data(self, name: str):
        file_name = LocalDirectoryStorage.FILE_PATH.format(name)
        if not aiof.os.path.exists(file_name):
            return strings.NOTFOUND
        await aiof.remove(file_name)
        return strings.DONE

    async def post_data(self, name: str, information: str):
        file_name = LocalDirectoryStorage.FILE_PATH.format(name)
        async with aiofiles.open(file_name, mode="w") as f:
            await f.write(information)
            await f.flush()
        return strings.DONE
