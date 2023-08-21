from datetime import datetime

from pymongo.collection import Collection

from model.youtube.core import YtVideo


class YtMongoRepository:
    def __init__(self, collection: Collection):
        self.collection = collection

    def upsert_video(self, video: YtVideo) -> bool:
        self.collection.update_one(
            {"video_id": video.video_id}, {"$set": video.model_dump()}, upsert=True
        )
        return True

    def add_if_doesnt_exist(self, video: YtVideo) -> bool:
        if not self.collection.find_one({"video_id": video.video_id}):
            self.collection.insert_one(video.model_dump())
            return True
        return False

    def update_if_exists(self, video: YtVideo) -> bool:
        if self.collection.find_one({"video_id": video.video_id}):
            self.collection.update_one(
                {"video_id": video.video_id},
                {"$set": video.model_dump()},
            )
            return True
        return False

    def get_video(self, video_id: str) -> YtVideo:
        return YtVideo(**self.collection.find_one({"video_id": video_id}))

    def get_videos_for_daterange(
        self, date_start: datetime.date, date_end: datetime.date
    ) -> list[YtVideo]:
        return [
            YtVideo(**video)
            for video in self.collection.find(
                {"published_at": {"$gte": date_start, "$lte": date_end}}
            )
        ]

    def find_all(self) -> list[YtVideo]:
        return [YtVideo(**video) for video in self.collection.find()]

    def get_videos_by_views(
        self, views_min: int, views_max: int = None
    ) -> list[YtVideo]:
        params = {"stats.views": {"$gte": views_min}}
        if views_max:
            params["stats.views"]["$lte"] = views_max

        return [YtVideo(**video) for video in self.collection.find(params)]


class YtMongoRepositoryFactory:
    def __init__(self, db_name: str, collection_name: str):
        import pymongo

        self.client = pymongo.MongoClient("mongodb://localhost:27017")
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def create(self) -> YtMongoRepository:
        return YtMongoRepository(self.collection)
