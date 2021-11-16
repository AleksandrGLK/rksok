from storage.local_storage import LocalDirectoryStorage
from storage.sqlstorage import SQLStorage

STORAGE_FACTORY = {
    "sql": SQLStorage(),
    "local_files": LocalDirectoryStorage(),
}

SERVER_ADDRESS = ("127.0.0.1", 7777)
PERMISSION_SERVER = ("vragi-vezde.to.digital", 51624)
ENCODING = "UTF-8"
MESSAGE_PATTERN = r"(.*?)\s(.*?|\s+)(?=\s\w{5}/1.0).*\s(.*)[.\r\n]*"
