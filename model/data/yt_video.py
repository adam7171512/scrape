import datetime

from pydantic import BaseModel

from model.data.stats import YtVideoStats


class YtVideo(BaseModel):
    video_id: str
    title: str
    channel: str
    date: datetime.datetime
    description: str | None = None
    stats: YtVideoStats | None = None
    transcript: str | None = None

    @classmethod
    def from_dict(cls, d):
        return cls(
            video_id=d.get("id").get("videoId"),
            channel=d.get("snippet").get("channelTitle"),
            title=d.get("snippet").get("title"),
            date=d.get("snippet").get("publishedAt"),
            description=d.get("snippet").get("description"),
        )

    @property
    def url(self):
        return f"https://www.youtube.com/watch?v={self.video_id}"
