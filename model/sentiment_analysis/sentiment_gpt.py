from gpt_tools.tools import GptContact
from model.sentiment_analysis.core import ISentimentRater, GptRating


class GptSentimentRater(ISentimentRater):
    # Todo: move to config
    MODEL = f"gpt-4"
    SYSTEM_MESSAGE = """
    Rate the text sentiment. Use values between -100 and 100
    ### Guidelines for rating: (but you can use value in between too) :
    -100 : very negative
    -50: negative
    0: neutral
    50: positive
    100: very positive
    ### Required answer format:
    sentiment_rating = <rating>
    """
    RETRY_LIMIT = 3

    def __init__(self, api_key: str):
        self.gpt = GptContact(api_key, self.MODEL)
        self.fail_count = 0

    def rate(self, text: str) -> GptRating:
        rating = self._get_gpt_sentiment_rating(text)

        if rating is None:
            if self.fail_count <= self.RETRY_LIMIT:
                self.fail_count += 1
                return self.rate(text)
            else:
                raise ValueError("Could not get valid gpt sentiment rating")

        self.fail_count = 0
        return GptRating(value=rating/100)

    def _get_gpt_sentiment_rating(self, text: str) -> float | None:
        rating = self.gpt.get_chat_completion(
            self.SYSTEM_MESSAGE, text, max_tokens=15, temperature=0
        )
        str_rating = ""
        # look for number in the response
        for char in rating:
            if char.isdigit() or char == "-":
                str_rating += char

        rating = int(str_rating)
        return rating if str_rating else None
