from typing import Protocol

import numpy as np
from scipy.special import softmax
from transformers import AutoConfig, AutoModelForSequenceClassification, AutoTokenizer

from model.data.sentiment import RobertaSentiment
from model.yt_tools.yt_mongo_repository import YtMongoRepository


class ISentimentRater(Protocol):
    def rate(self, text: str) -> RobertaSentiment:
        ...


class RobertaSentimentRater(ISentimentRater):
    MODEL = f"cardiffnlp/twitter-roberta-base-sentiment"

    def __init__(self, repository: YtMongoRepository):
        self.model = AutoModelForSequenceClassification.from_pretrained(self.MODEL)
        self.tokenizer = AutoTokenizer.from_pretrained(self.MODEL)
        self.config = AutoConfig.from_pretrained(self.MODEL)
        self.repository = repository

    def get_roberta_sentiment(self, text: str) -> dict:
        encoded_input = self.tokenizer(text, return_tensors="pt", max_length=510)
        output = self.model(**encoded_input)
        scores = output[0][0].detach().numpy()
        scores = softmax(scores)
        ranking = np.argsort(scores)
        rank_scores = dict(zip(ranking, scores[ranking]))
        return {
            "positive": float(rank_scores[2]),
            "neutral": float(rank_scores[1]),
            "negative": float(rank_scores[0]),
        }

    def assign_roberta_sentiment_for_all(self, overwrite: bool = False):
        for vid in self.repository.find_all():
            # if roberta sentiment already there, skip
            if vid.stats.sentiment_roberta and not overwrite:
                continue

            roberta_title_sentiment = self.get_roberta_sentiment(vid.title)
            rs = RobertaSentiment(
                title_pos=roberta_title_sentiment["positive"],
                title_neu=roberta_title_sentiment["neutral"],
                title_neg=roberta_title_sentiment["negative"],
            )

            if vid.transcript:
                roberta_transcript_sentiment = self.get_roberta_sentiment(
                    vid.transcript
                )
                rs.transcript_pos = roberta_transcript_sentiment["positive"]
                rs.transcript_neu = roberta_transcript_sentiment["neutral"]
                rs.transcript_neg = roberta_transcript_sentiment["negative"]

            vid.stats.sentiment_roberta = rs
            print(f"updated {vid.title}")
            self.repository.update_if_exists(vid)
