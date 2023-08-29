from datetime import datetime

import toml
from pymongo import MongoClient

from model.youtube.yt_data_scraper import YtDataCollector

client = MongoClient("mongodb://localhost:27017")

config = toml.load("config.toml")
API_KEYS = config["api"]["yt_data_api_keys"]

yt_scraper = YtDataCollector(db_client=client, api_keys=API_KEYS)

yt_scraper.collect_data(
    db_name="youtube",
    collection_name="atom",
    topic="cryptocurrency atom",
    date_start=datetime(2023, 1, 1).date(),
    date_end=datetime(2023, 7, 29).date(),
    time_delta=1,
    max_results_per_time_delta=5,
    language="en",
    stats_lower_limit=1000,
    length_minutes_lower_limit=4,
)
