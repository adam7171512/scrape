from typing import Protocol

from pydantic import BaseModel


class GptSentiment(BaseModel):
    title: float
    transcript: float | None = None


class SentimentRating(BaseModel):
    @property
    def score(self) -> float:
        raise NotImplementedError


class GptRating(SentimentRating):
    value: float

    @property
    def score(self) -> float:
        return self.value


class RobertaRating(SentimentRating):
    negative: float
    neutral: float
    positive: float

    @property
    def score(self) -> float:
        return -1 * self.negative + 0 * self.neutral + 1 * self.positive


class RobertaSentiment(BaseModel):
    title_pos: float
    title_neg: float
    title_neu: float
    transcript_pos: float | None = None
    transcript_neg: float | None = None
    transcript_neu: float | None = None
