import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets" / "images"
LOCAL_CONFIG_PATH = BASE_DIR / "bot.local.json"
BATTLE_BASELINE_PATH = BASE_DIR / "battle_baseline.png"
ROUTE_PATH = BASE_DIR / "route.json"

PROCESS_NAME = "PokeAlliance_gl.exe"
WINDOW_NAME = "PokeAlliance - Lippeh"

POS_BASE_OFFSET = 0x0027D168

OFFSET_X = 0x0
OFFSET_Y = 0x4
OFFSET_Z = 0x8

KEY_W = 0x57
KEY_A = 0x41
KEY_S = 0x53
KEY_D = 0x44
KEY_F = 0x46
KEY_I = 0x49
KEY_O = 0x4F
KEY_R = 0x52
KEY_X = 0x58

MOVE_TIMEOUT_SECONDS = 10
MOVE_STALL_LIMIT = 20
AUTO_CATCH_COOLDOWN_SECONDS = 0.5
AUTO_CATCH_CLEAR_TIMEOUT_SECONDS = 5
AUTO_CATCH_CLEAR_CHECK_INTERVAL_SECONDS = 0.1
AUTO_CATCH_POST_MOVE_DELAY_SECONDS = 0.01
AUTO_CATCH_LOOP_INTERVAL_SECONDS = 0.1
AUTO_CATCH_CLEAR_CONFIRMATIONS = 6
AUTO_CATCH_MIN_SCAN_AFTER_BATTLE_SECONDS = 2
AUTO_CATCH_MIN_SCAN_AFTER_THROW_SECONDS = 2
AUTO_CATCH_POST_BATTLE_MAX_DURATION_SECONDS = 20
AUTO_CATCH_REQUIRED_CLEAR_WINDOW_SECONDS = 1
DETECTION_REGION_OFFSET = (5, 157, 1072, 561)
DETECTION_CONFIDENCE = 0.6
DETECTION_GRAYSCALE_FALLBACK = True
DETECTION_COLOR_MATCH_MAX_SCORE = 80
BATTLE_IMAGE_DIFF_THRESHOLD = 8
BATTLE_STOP_WAIT_TIMEOUT_SECONDS = 2
BATTLE_STOP_STABLE_READS = 3
BATTLE_STOP_POLL_INTERVAL_SECONDS = 0.05
BATTLE_PRE_ACTION_DELAY_SECONDS = 4 #tempo de espera ate comecar o fluxo de atk
BATTLE_POST_ACTION_DELAY_SECONDS = 5
BATTLE_CHECK_INTERVAL_SECONDS = 0.05
BATTLE_RESUME_AFTER_R_DELAY_SECONDS = 0.2
RESUME_KEY_DEBOUNCE_SECONDS = 1.5
PATH_RETRY_ATTEMPTS = 3
PATH_RETRY_DELAY_SECONDS = 0.5
PATH_DETOUR_DISTANCE = 1

HOTKEY_RECORD = "shift+r"
HOTKEY_STOP = "shift+s"
HOTKEY_PLAY = "shift+p"
HOTKEY_CATCH = "shift+c"
HOTKEY_MARK_TOP_LEFT = "shift+1"
HOTKEY_MARK_BOTTOM_RIGHT = "shift+2"
HOTKEY_CLEAR_REGION = "shift+3"
HOTKEY_MARK_BATTLE_TOP_LEFT = "shift+4"
HOTKEY_MARK_BATTLE_BOTTOM_RIGHT = "shift+5"
HOTKEY_CAPTURE_BATTLE_BASELINE = "shift+6"
HOTKEY_MARK_FLOW_POINT = "shift+7"
HOTKEY_START_BATTLE_MONITOR = "shift+b"
HOTKEY_STOP_BATTLE_MONITOR = "shift+n"
HOTKEY_CLEAR_BATTLE_CONFIG = "shift+0"

POKEMON_IMAGE_NAMES = [
    "pokemon.png",
    "pokemon1.png",
    "pokemon2.png",
    "pokemon3.png",
]


def get_pokemon_images():
    image_paths = []
    seen = set()

    candidate_dirs = [ASSETS_DIR, BASE_DIR]

    for directory in candidate_dirs:
        if directory.exists():
            for image_path in sorted(directory.glob("pokemon*.png")):
                normalized = str(image_path)
                if normalized not in seen:
                    image_paths.append(normalized)
                    seen.add(normalized)

    for image_name in POKEMON_IMAGE_NAMES:
        for directory in candidate_dirs:
            image_path = directory / image_name
            normalized = str(image_path)

            if image_path.exists() and normalized not in seen:
                image_paths.append(normalized)
                seen.add(normalized)

    return image_paths


def load_local_config():
    if not LOCAL_CONFIG_PATH.exists():
        return {}

    try:
        with LOCAL_CONFIG_PATH.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError):
        return {}


def save_local_config(data):
    with LOCAL_CONFIG_PATH.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def get_detection_region_override():
    data = load_local_config()
    region = data.get("detection_region")

    if not region or len(region) != 4:
        return None

    return tuple(int(value) for value in region)


def set_detection_region_override(region):
    data = load_local_config()
    data["detection_region"] = [int(value) for value in region]
    save_local_config(data)


def clear_detection_region_override():
    data = load_local_config()
    data.pop("detection_region", None)
    save_local_config(data)


def get_battle_region():
    data = load_local_config()
    region = data.get("battle_region")

    if not region or len(region) != 4:
        return None

    return tuple(int(value) for value in region)


def set_battle_region(region):
    data = load_local_config()
    data["battle_region"] = [int(value) for value in region]
    save_local_config(data)


def clear_battle_region():
    data = load_local_config()
    data.pop("battle_region", None)
    save_local_config(data)


def get_battle_baseline_color():
    return None


def set_battle_baseline_color(color):
    return None


def clear_battle_baseline_color():
    if BATTLE_BASELINE_PATH.exists():
        BATTLE_BASELINE_PATH.unlink()


def has_battle_baseline_image():
    return BATTLE_BASELINE_PATH.exists()
