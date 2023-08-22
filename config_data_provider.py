import os

import toml


def get_yt_api_keys() -> list[str]:
    path = os.path.dirname(os.path.abspath(__file__))
    config = toml.load(f"{path}/config.toml")
    api_keys = config["api"]["yt_data_api_keys"]
    return api_keys


def get_open_ai_api_key() -> str:
    path = os.path.dirname(os.path.abspath(__file__))
    config = toml.load(f"{path}/config.toml")
    api_key = config["api"]["open_ai_api_key"]
    return api_key
