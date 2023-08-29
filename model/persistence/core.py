import datetime
from typing import Protocol

from model.youtube.core import YtVideo


class IYtVideoRepository(Protocol):
    def add_or_update(self, video: YtVideo) -> bool:
        ...

    def add_if_doesnt_exist(self, video: YtVideo) -> bool:
        ...

    def update_if_exists(self, video: YtVideo) -> bool:
        ...

    def get_video(self, video_id: str) -> YtVideo:
        ...

    def get_videos_by_date(
        self, date_from: datetime.date, date_to: datetime.date
    ) -> list[YtVideo]:
        ...

    def get_videos_by_views(
        self, views_min: int, views_max: int = None
    ) -> list[YtVideo]:
        ...

    def get_all_videos(self) -> list[YtVideo]:
        ...
