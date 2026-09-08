import json as ujson

CONFIG_CACHE: dict | None = None


def load_config(file_path: str = "data/config.json", force: bool = False) -> dict:
    """
    Load the configuration from a JSON file.

    Args:
        file_path (str): The path to the configuration file. Defaults to "data/config.json".
        force (bool): If True, forces reloading the configuration even if it's cached. Defaults to False.

    Returns:
        dict: The loaded configuration as a dictionary.
    """
    global CONFIG_CACHE

    if CONFIG_CACHE is not None and not force:
        return CONFIG_CACHE

    try:
        with open(file_path, "r") as f:
            CONFIG_CACHE = ujson.load(f)  # pyright: ignore[reportConstantRedefinition]
            if CONFIG_CACHE is None:
                CONFIG_CACHE = {}  # pyright: ignore[reportConstantRedefinition]
            return CONFIG_CACHE
    except FileNotFoundError as e:
        print(f"Error loading configuration from {file_path}: {e}")
        return {}


def save_config(override: dict, file_path: str = "data/config.json") -> bool:
    """
    Save the configuration to a JSON file.

    Args:
        config (dict): The configuration to save.
        file_path (str): The path to the configuration file. Defaults to "data/config.json".
    """
    global CONFIG_CACHE

    config = load_config(file_path)
    config["utc"] = override.get("utc", config.get("utc", 7))
    config["language"] = override.get("language", config.get("language", "en"))
    config["wifi"] = override.get(
        "wifi", config.get("wifi", {"ssid": "", "password": ""})
    )

    try:
        with open(file_path, "w") as f:
            ujson.dump(config, f)
            CONFIG_CACHE = config  # pyright: ignore[reportConstantRedefinition]
            return True
    except Exception as e:  # noqa: BLE001
        print(f"Error saving configuration to {file_path}: {e}")
        return False
