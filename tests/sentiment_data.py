import os
from enum import Enum


class SentimentRating(Enum):
    VERY_NEGATIVE = 1
    NEGATIVE = 2
    NEUTRAL = 3
    POSITIVE = 4
    VERY_POSITIVE = 5

def read_sentiment_data(sentiment_rating: SentimentRating) -> list[str]:
    """
    Return list of strings with particular sentiment type for test purposes
    """
    # Determine the path to the file
    current_dir = os.path.dirname(__file__)  # Gets the directory of the current .py file
    file_path = os.path.join(current_dir, 'resources', 'sentiment_data', 'assets', f'{sentiment_type}.txt')

    # Read and return the file contents
    with open(file_path, 'r') as file:
        return file.readlines()