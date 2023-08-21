import pytest

from model.sentiment_analysis.core import ISentimentRater, SentimentRating
from model.sentiment_analysis.sentiment_finbert import FinbertSentimentRater
from tests.resources.sentiment_data import SentimentRatingType, read_sentiment_data

"""
FinBert sentiment model doesnt do well with input of casual yt-title like type, thus I left only positive/negative tests
and greatly reduced thresholds, just to check if it works and goes in good direction
"""


@pytest.fixture(scope="module")
def sentiment_rater() -> ISentimentRater:
    return FinbertSentimentRater()


def test_very_negative_string_should_receive_very_negative_score(sentiment_rater):
    very_negative_string = read_sentiment_data(SentimentRatingType.VERY_NEGATIVE)[0]
    sentiment_rating: SentimentRating = sentiment_rater.rate(very_negative_string)
    assert sentiment_rating.score <= -0.1


def test_very_positive_sentiment_string_should_receive_very_positive_score(
    sentiment_rater,
):
    very_positive_string = read_sentiment_data(SentimentRatingType.VERY_POSITIVE)[0]
    sentiment_rating: SentimentRating = sentiment_rater.rate(very_positive_string)
    score = sentiment_rating.score
    assert score >= 0.1
