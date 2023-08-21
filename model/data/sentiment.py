from pydantic import BaseModel


class GptSentiment(BaseModel):
    title: float
    transcript: float | None = None


class RobertaRating(BaseModel):
    negative: float
    neutral: float
    positive: float

    @property
    def score(self):
        return -1 * self.negative + 0 * self.neutral + 1 * self.positive


class RobertaSentiment(BaseModel):
    title_pos: float
    title_neg: float
    title_neu: float
    transcript_pos: float | None = None
    transcript_neg: float | None = None
    transcript_neu: float | None = None
