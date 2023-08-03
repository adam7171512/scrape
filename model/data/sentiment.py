from pydantic import BaseModel


class GptSentiment(BaseModel):
    title: float
    transcript: float | None = None


class RobertaSentiment(BaseModel):
    title_pos: float
    title_neg: float
    title_neu: float
    transcript_pos: float | None = None
    transcript_neg: float | None = None
    transcript_neu: float | None = None
