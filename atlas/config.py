import json

from atlas.paths import get_config_path


CONFIG_FILE = get_config_path()


DEFAULT_CONFIG = {
    "user_name": "User",
    "assistant_name": "Atlas",
    "local_model": "qwen2.5:7b",
    "setup_complete": False
}


def config_exists():
    return CONFIG_FILE.exists()


def get_config():
    if not CONFIG_FILE.exists():
        with open(CONFIG_FILE, "w") as file:
            json.dump(DEFAULT_CONFIG, file, indent=4)

        return DEFAULT_CONFIG

    with open(CONFIG_FILE, "r") as file:
        config = json.load(file)

    return {**DEFAULT_CONFIG, **config}


def save_config(config):
    config = {**DEFAULT_CONFIG, **config}

    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file, indent=4)


def needs_first_run_setup():
    if not config_exists():
        return True

    config = get_config()

    if config.get("setup_complete") is True:
        return False

    user_name = config.get("user_name", "").strip()
    assistant_name = config.get("assistant_name", "").strip()
    local_model = config.get("local_model", "").strip()

    default_user_names = {"", "User", "Your Name"}

    if user_name not in default_user_names and assistant_name and local_model:
        return False

    return True


def get_user_name():
    return get_config()["user_name"]


def get_assistant_name():
    return get_config()["assistant_name"]


def get_local_model():
    return get_config()["local_model"]
