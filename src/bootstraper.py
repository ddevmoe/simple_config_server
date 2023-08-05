from src.common import config
from src.loaders import LocalFolderLoader
from src.parser import ConfigParser
from src.store import ConfigStore


def bootstrap() -> ConfigStore:
    parser = ConfigParser()
    loader = LocalFolderLoader(parser, config.LOCAL_FOLDER_LOADER_PATH)
    store = ConfigStore(loader)

    return store
