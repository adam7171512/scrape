import numpy as np
from scipy.special import softmax
from transformers import (AutoConfig, AutoModelForSequenceClassification,
                          AutoTokenizer)

from model.sentiment_analysis.core import ISentimentRater, SplitScoreRating

"""
Warning! FinBert is likely bad option for rating youtube-title-like text sentiment
rating, as it was trained on more official financial text
"""


class FinbertSentimentRater(ISentimentRater):
    MODEL = f"ProsusAI/finbert"

    def __init__(self):
        self.model = AutoModelForSequenceClassification.from_pretrained(self.MODEL)
        self.tokenizer = AutoTokenizer.from_pretrained(self.MODEL)
        self.config = AutoConfig.from_pretrained(self.MODEL)

    def rate(self, text: str) -> SplitScoreRating:
        encoded_input = self.tokenizer(text, return_tensors="pt", max_length=510)
        output = self.model(**encoded_input)
        scores = output[0][0].detach().numpy()
        scores = softmax(scores)
        ranking = np.argsort(scores)
        rank_scores = dict(zip(ranking, scores[ranking]))

        sentiment_rating: SplitScoreRating = SplitScoreRating(
            negative=float(rank_scores[1]),
            neutral=float(rank_scores[2]),
            positive=float(rank_scores[0]),
        )
        return sentiment_rating

    @property
    def model_name(self) -> str:
        return self.MODEL