from pydantic import BaseModel

from model.data.sentiment import GptSentiment, RobertaSentiment


class YtVideoStats(BaseModel):
    views: int = None
    comments: int = None
    likes: int = None
    length_minutes: float = None
    sentiment_gpt: GptSentiment | None = None
    sentiment_roberta: RobertaSentiment | None = None