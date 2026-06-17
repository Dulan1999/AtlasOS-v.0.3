import os
from pathlib import Path


APP_NAME = "AtlasOS"


def get_user_data_dir():
    if os.name == "nt":
        base_dir = os.getenv("APPDATA")

        if not base_dir:
            base_dir = Path.home() / "AppData" / "Roaming"
        else:
            base_dir = Path(base_dir)

    else:
        base_dir = Path.home() / ".local" / "share"

    data_dir = base_dir / APP_NAME
    data_dir.mkdir(parents=True, exist_ok=True)

    return data_dir


def get_config_path():
    return get_user_data_dir() / "config.json"


def get_semantic_memory_path():
    return get_user_data_dir() / "knowledge.json"


def get_episodic_memory_path():
    return get_user_data_dir() / "memories.json"


def get_procedural_memory_path():
    return get_user_data_dir() / "procedures.json"