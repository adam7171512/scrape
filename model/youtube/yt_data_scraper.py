from datetime import datetime

from pymongo import MongoClient

from model.youtube.yt_mongo_repository import YtMongoRepository
from model.youtube.yt_top_vid_finder import YtFinder


class YtScraper:
    def __init__(self, db_client: MongoClient, api_keys: list[str]):
        self.db_client = db_client
        self.api_keys = api_keys

    def scrape(
        self,
        db_name: str,
        collection_name: str,
        topic: str,
        date_start: datetime.date,
        date_end: datetime.date,
        time_delta: int,
        max_results_per_time_delta: int = 10,
        language: str = None,
        stats_lower_limit: int | None = None,
        length_minutes_lower_limit: int | None = None,
    ):
        scraper = YtFinder(api_keys=self.api_keys)
        vids = scraper.scrape_top_videos_with_stats(
            topic=topic,
            date_start=date_start,
            date_end=date_end,
            time_delta=time_delta,
            max_results_per_time_delta=max_results_per_time_delta,
            language=language,
            stats_lower_limit=stats_lower_limit,
            length_minutes_lower_limit=length_minutes_lower_limit,
        )
        db = self.db_client[db_name]
        collection = db[collection_name]
        repo = YtMongoRepository(collection)

        for video_batch in vids:
            for video in video_batch:
                repo.add_if_doesnt_exist(video)
