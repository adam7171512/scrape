import numpy as np
from scipy.special import softmax
from transformers import (AutoConfig, AutoModelForSequenceClassification,
                          AutoTokenizer)

from model.sentiment_analysis.core import ISentimentRater, SplitScoreRating
from model.youtube.persistence.mongo import YtVideoMongoRepository


class RobertaSentimentRater(ISentimentRater):
    """
    Sentiment rater implementation based on Roberta model. Suitable only for rating short text.
    """

    MODEL = f"cardiffnlp/twitter-roberta-base-sentiment"

    def __init__(self, repository: YtVideoMongoRepository | None = None):
        self.model = AutoModelForSequenceClassification.from_pretrained(self.MODEL)
        self.tokenizer = AutoTokenizer.from_pretrained(self.MODEL)
        self.config = AutoConfig.from_pretrained(self.MODEL)
        self.repository = repository

    def rate(self, text: str) -> SplitScoreRating:
        encoded_input = self.tokenizer(text, return_tensors="pt", max_length=510)
        output = self.model(**encoded_input)
        scores = output[0][0].detach().numpy()
        scores = softmax(scores)
        ranking = np.argsort(scores)
        rank_scores = dict(zip(ranking, scores[ranking]))
        return SplitScoreRating(
            negative=float(rank_scores[0]),
            neutral=float(rank_scores[1]),
            positive=float(rank_scores[2]),
        )

    @property
    def model_name(self) -> str:
        return self.MODEL
