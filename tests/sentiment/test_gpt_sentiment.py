import pytest

from model.data.sentiment import ISentimentRater, SentimentRating
from model.trash_utils.sentiment_analysis.sentiment_gpt import GptSentimentRater
from tests.sentiment_data import SentimentRatingType, read_sentiment_data


@pytest.fixture(scope="module")
def sentiment_rater() -> ISentimentRater:
    return GptSentimentRater()


def test_very_negative_string_should_receive_very_negative_score(sentiment_rater):
    very_negative_string = read_sentiment_data(SentimentRatingType.VERY_NEGATIVE)[0]
    gpt_sentiment_rating: SentimentRating = sentiment_rater.rate(very_negative_string)
    assert gpt_sentiment_rating.score <= -0.5


def test_neutral_sentiment_string_should_receive_neutral_score(sentiment_rater):
    neutral_string = read_sentiment_data(SentimentRatingType.NEUTRAL)[0]
    gpt_sentiment_rating: SentimentRating = sentiment_rater.rate(neutral_string)
    score = gpt_sentiment_rating.score
    assert -0.25 <= score <= 0.25


def test_very_positive_sentiment_string_should_receive_very_positive_score(
    sentiment_rater,
):
    very_positive_string = read_sentiment_data(SentimentRatingType.VERY_POSITIVE)[0]
    gpt_sentiment_rating: SentimentRating = sentiment_rater.rate(very_positive_string)
    score = gpt_sentiment_rating.score
    assert score >= 0.5
