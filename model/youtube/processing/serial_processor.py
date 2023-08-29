import datetime
import logging

from model.sentiment_analysis.core import ISentimentRater
from model.youtube.core import YtVideo, YoutubeVideoSentimentRating
from model.persistence import IYtVideoRepository
from model.youtube.processing.core import IYtVidScrapingProcessor
from model.youtube.yt_top_vid_finder import YtTopVideoFinder
from model.youtube.yt_transcript_scraper import IYtTranscriptScraper


class YtVidScrapingSerialProcessor(IYtVidScrapingProcessor):
    """
    This class is responsible for conducting video search on particular topic,
    scraping the video's stats, transcript, and rating the video's sentiment.
    Then it saves the data to the database using repository.

    The processing is done in a serial manner, meaning that the next
    video is processed only after whole pipeline is done for the previous video.
    """

    def __init__(self,
                 repository: IYtVideoRepository,
                 yt_finder: YtTopVideoFinder,
                 transcript_scraper: IYtTranscriptScraper,
                 sentiment_rater: ISentimentRater,
                 ):
        self.repository = repository
        self.yt_finder = yt_finder
        self.transcript_scraper = transcript_scraper
        self.sentiment_rater = sentiment_rater

    def process(
            self,
            topic: str,
            date_start: datetime.date,
            date_end: datetime.date,
            time_delta: int,
            max_results_per_time_delta: int = 10,
            language: str = None,
            stats_lower_limit: int | None = None,
            length_minutes_lower_limit: int | None = None,
    ) -> None:

        videos_list_generator = self.yt_finder.scrape_top_videos_with_stats(
            topic=topic,
            date_start=date_start,
            date_end=date_end,
            time_delta=time_delta,
            max_results_per_time_delta=max_results_per_time_delta,
            language=language,
            stats_lower_limit=stats_lower_limit,
            length_minutes_lower_limit=length_minutes_lower_limit,
        )

        for videos_list in videos_list_generator:
            for video in videos_list:
                self._process_video(video)

    def _process_video(self, video: YtVideo):
        transcript = self.transcript_scraper.scrape_transcript(video.video_id)
        video.transcript = transcript

        title_sentiment_rating = self.sentiment_rater.rate(video.title).score
        transcript_sentiment_rating = self.sentiment_rater.rate(transcript).score

        sentiment_rating = YoutubeVideoSentimentRating(
            model=self.sentiment_rater.model_name,
            score_title=title_sentiment_rating,
            score_transcript=transcript_sentiment_rating,
        )

        video.stats.sentiment_rating = sentiment_rating

        self._save_video(video)
        logging.log(logging.INFO, f"Video {video.video_id} was processed and saved to the database.")

    def _save_video(self, video: YtVideo):
        added = self.repository.add_if_doesnt_exist(video)

        if not added:
            logging.log(logging.ERROR, f"Video {video.video_id} already exists in the database.")

    def _update_video(self, video: YtVideo):
        updated = self.repository.update_if_exists(video)

        if not updated:
            logging.log(logging.ERROR, f"Video {video.video_id} doesn't exist in the database.")
