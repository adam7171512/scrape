import os

import toml

path = os.path.dirname(os.path.abspath(__file__))


def get_config() -> dict:
    return toml.load(f"{path}/config.toml")


def get_yt_api_keys() -> list[str]:
    config = toml.load(f"{path}/config.toml")
    api_keys = config["api"]["yt_data_api_keys"]
    return api_keys


def get_open_ai_api_key() -> str:
    config = toml.load(f"{path}/config.toml")
    api_key = config["api"]["open_ai_api_key"]
    return api_key


def get_mongo_db_url() -> str:
    config = toml.load(f"{path}/config.toml")
    db_url = config["db"]["mongo_db_url"]
    return db_url


def get_scraper_config() -> dict:
    config = toml.load(f"{path}/config.toml")
    return config["scraper"]


def get_db_config(db_type: str) -> dict:
    config = toml.load(f"{path}/config.toml")
    return config[db_type]
