from datetime import datetime

from pymongo.collection import Collection

from model.youtube.core import YtVideo
from model.youtube.persistence.core import IYtVideoRepository


class YtVideoMongoRepository(IYtVideoRepository):
    def __init__(self, collection: Collection):
        self.collection = collection

    def add_or_update(self, video: YtVideo) -> bool:
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

    def get_video(self, video_id: str) -> YtVideo | None:
        result = self.collection.find_one({"video_id": video_id})
        if result:
            return YtVideo(**result)
        return None

    def get_videos_by_date(
        self, date_start: datetime.date, date_end: datetime.date
    ) -> list[YtVideo]:
        return [
            YtVideo(**video)
            for video in self.collection.find(
                {"published_at": {"$gte": date_start, "$lte": date_end}}
            )
        ]

    def get_all_videos(self) -> list[YtVideo]:
        return [YtVideo(**video) for video in self.collection.find()]

    def get_videos_by_views(
        self, views_min: int, views_max: int = None
    ) -> list[YtVideo]:
        params = {"stats.views": {"$gte": views_min}}
        if views_max:
            params["stats.views"]["$lte"] = views_max

        return [YtVideo(**video) for video in self.collection.find(params)]
