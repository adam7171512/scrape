import datetime
from typing import Protocol

from pydantic import BaseModel


def get_url_for_vid_id(vid_id: str) -> str:
    return f"https://www.youtube.com/watch?v={vid_id}"


class YoutubeVideoSentimentRating(BaseModel):
    model: str
    score_title: float
    score_transcript: float | None = None


class YtVideoStats(BaseModel):
    views: int = None
    comments: int = None
    likes: int = None
    length_minutes: float = None
    sentiment_rating: YoutubeVideoSentimentRating | None = None


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
        return get_url_for_vid_id(self.video_id)


class IYtStatsScraper(Protocol):
    def scrape_stats(self, video_id: str) -> YtVideoStats:
        ...


class IYtTranscriptScraper(Protocol):

    def scrape_transcript(self, video_id: str) -> str | None:
        ...
