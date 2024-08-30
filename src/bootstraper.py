from src.common import config
from src.deserializers import JsonDeserializer
from src.readers import LocalFolderReader
from src.parser import ConfigParser
from src.store import ConfigStore


def bootstrap() -> ConfigStore:
    parser = ConfigParser()
    desealizer = JsonDeserializer()
    reader = LocalFolderReader(desealizer, config.LOCAL_FOLDER_LOADER_PATH)
    store = ConfigStore(reader, parser)

    return store
