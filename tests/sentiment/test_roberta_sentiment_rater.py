import pytest
from model.trash_utils.sentiment_analysis.sentiment_roberta import RobertaSentimentRater, \
    RobertaRating
from tests.sentiment_data import read_sentiment_data, SentimentRating


@pytest.fixture(scope="module")
def rsr():
    return RobertaSentimentRater()


def test_very_negative_string_should_receive_very_negative_score(rsr):
    very_negative_string = read_sentiment_data(SentimentRating.VERY_NEGATIVE)[0]
    roberta_sentiment_rating: RobertaRating = rsr.get_roberta_sentiment(very_negative_string)
    assert roberta_sentiment_rating.score < -0.75


def test_neutral_sentiment_string_should_receive_neutral_score(rsr):
    neutral_string = read_sentiment_data(SentimentRating.NEUTRAL)[0]
    roberta_sentiment_rating: RobertaRating = rsr.get_roberta_sentiment(neutral_string)
    score = roberta_sentiment_rating.score
    assert -0.2 < score < 0.2


def test_very_positive_sentiment_string_should_receive_very_positive_score(rsr):
    very_positive_string = read_sentiment_data(SentimentRating.VERY_POSITIVE)[0]
    roberta_sentiment_rating: RobertaRating = rsr.get_roberta_sentiment(very_positive_string)
    score = roberta_sentiment_rating.score
    assert score > 0.8
