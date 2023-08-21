import os
from enum import Enum


class SentimentRatingType(Enum):
    VERY_NEGATIVE = "very_negative"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"
    VERY_POSITIVE = "very_positive"


def read_sentiment_data(sentiment_rating: SentimentRatingType) -> list[str]:
    """
    Return list of strings of particular sentiment type for test purposes
    """
    base_dir = os.path.dirname(os.path.dirname(__file__))
    file_path = os.path.join(
        base_dir,
        "tests",
        "resources",
        "sentiment_data",
        "assets",
        f"{sentiment_rating.value}.txt",
    )

    # Read and return the file contents
    with open(file_path, "r", encoding="utf-8") as file:
        return file.readlines()
