from model.persistence.core import IYtVideoRepository
from model.sentiment_analysis.core import ISentimentRater
from model.youtube.core import YtVideo, YoutubeVideoSentimentRating


class SentimentFiller:
    """
    Class responsible for filling out missing sentiment data for videos in repository
    """

    def __init__(
            self,
            yt_sentiment_rater: ISentimentRater,
            yt_repository: IYtVideoRepository,
            overwrite_existing_data: bool,
    ):
        self.sentiment_rater = yt_sentiment_rater
        self.yt_repository = yt_repository
        self.overwrite_existing_data = overwrite_existing_data

    def fill_sentiment(self, video: YtVideo) -> None:

        title_sentiment_rating = None
        transcript_sentiment_rating = None
        if video.stats.sentiment_rating and not self.overwrite_existing_data:
            title_sentiment_rating = video.stats.sentiment_rating.score_title
            transcript_sentiment_rating = video.stats.sentiment_rating.score_transcript

        if title_sentiment_rating is None:
            title_sentiment_rating = self.sentiment_rater.rate(video.title).score

        if video.transcript and transcript_sentiment_rating is None:
            transcript_sentiment_rating = self.sentiment_rater.rate(video.transcript).score

        sentiment_rating = YoutubeVideoSentimentRating(
            model=self.sentiment_rater.model_name,
            score_title=title_sentiment_rating,
            score_transcript=transcript_sentiment_rating,
        )

        video.stats.sentiment_rating = sentiment_rating
        self.yt_repository.update_if_exists(video)

    def fill_missing_sentiment_ratings(self):
        for vid in self.yt_repository.get_all_videos():
            if self._sentiment_data_incomplete(vid):
                self.fill_sentiment(vid)

    def _sentiment_data_incomplete(self, video: YtVideo) -> bool:
        return video.stats.sentiment_rating is None or \
            video.stats.sentiment_rating.score_title is None or \
            video.stats.sentiment_rating.score_transcript is None
