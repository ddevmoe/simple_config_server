import os


HTTP_PORT = int(os.environ.get('HTTP_PORT', 8080))
LOCAL_FOLDER_LOADER_PATH = os.environ.get('LOCAL_CONFIG_FOLDER_PATH', './configs')
