import json
from actions.utils import get_file_content

DATA_PATH = "./data"

MENU = json.load(get_file_content(f"{DATA_PATH}/menu.json"))
OPENING_HOURS = json.load(get_file_content(f"{DATA_PATH}/opening_hours.json"))
