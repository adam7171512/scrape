from typing import Protocol

from pydantic import BaseModel


class SentimentRating(BaseModel):
    @property
    def score(self) -> float:
        raise NotImplementedError


class GptRating(SentimentRating):
    value: float

    @property
    def score(self) -> float:
        return self.value


class SplitScoreRating(SentimentRating):
    negative: float
    neutral: float
    positive: float

    @property
    def score(self) -> float:
        return -1 * self.negative + 0 * self.neutral + 1 * self.positive


class ISentimentRater(Protocol):
    def rate(self, text: str) -> SentimentRating:
        ...

