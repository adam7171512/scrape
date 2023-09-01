import datetime
import logging

from model.persistence.core import IYtVideoRepository
from model.pipeline.core import IYtVidScrapingPipeline
from model.sentiment_analysis.core import ISentimentRater
from model.youtube.core import (IYtTopVideoFinder, YoutubeVideoSentimentRating,
                                YtVideo)
from model.youtube.yt_top_vid_finder import YtTopVideoFinder
from model.youtube.yt_transcript_scraper import IYtTranscriptScraper


class YtVidScrapingStdPipeline(IYtVidScrapingPipeline):
    """
    This class is responsible for conducting video search on particular topic,
    scraping the video's stats, transcript, and rating the video's sentiment.
    Then it saves the data to the database using repository.

    This implementation follows the pipeline:
    1. Find the videos and their stats
    2. Scrape the transcript
    3. Analyse the sentiment and update the sentiment stats
    """

    def __init__(
        self,
        repository: IYtVideoRepository,
        yt_finder: IYtTopVideoFinder,
        transcript_scraper: IYtTranscriptScraper,
        sentiment_rater: ISentimentRater,
        overwrite_existing_data: bool,
    ):
        self.repository = repository
        self.yt_finder = yt_finder
        self.transcript_scraper = transcript_scraper
        self.sentiment_rater = sentiment_rater
        self.overwrite_existing_data = overwrite_existing_data

    def process(
        self,
        topic: str,
        date_start: datetime.date,
        date_end: datetime.date,
        time_delta: int,
        max_results_per_time_delta: int = 10,
        language: str = "en",
        stats_lower_limit: int | None = None,
        length_minutes_lower_limit: int = 5,
    ) -> None:
        videos_list_generator = self.yt_finder.scrape_top_videos_with_stats(
            topic=topic,
            date_start=date_start,
            date_end=date_end,
            time_delta=time_delta,
            max_results_per_time_delta=max_results_per_time_delta,
            language=language,
            min_views=stats_lower_limit,
            min_video_length=length_minutes_lower_limit,
        )

        processed = []

        for video_batch in videos_list_generator:
            processed.extend(self._add_videos_to_database(video_batch))

        processed = self._add_videos_to_database(processed)

        transcript_scraped = []

        for video in processed:
            self._scrape_transcript(video)
            transcript_scraped.append(video)

        for video in transcript_scraped:
            self._rate_sentiment(video)

    # todo: refactor this to use batch operations
    def _add_videos_to_database(self, videos: list[YtVideo]):
        vids = []
        if self.overwrite_existing_data:
            for video in videos:
                self.repository.add_or_update(video)
            vids = videos
        else:
            for video in videos:
                v = self.repository.get_video(video.video_id)
                if v:
                    vids.append(v)
                else:
                    self._save_video(video)
                    vids.append(video)
        return vids

    def _save_video(self, video: YtVideo):
        added = self.repository.add_if_doesnt_exist(video)

        if not added:
            logging.log(
                logging.ERROR, f"Video {video.video_id} already exists in the database."
            )

    def _update_video(self, video: YtVideo):
        updated = self.repository.update_if_exists(video)

        if not updated:
            logging.log(
                logging.ERROR, f"Video {video.video_id} doesn't exist in the database."
            )

    def _scrape_transcript(self, video: YtVideo):
        transcript = video.transcript
        if transcript is None or self.overwrite_existing_data:
            transcript = self.transcript_scraper.scrape_transcript(video.video_id)

        video.transcript = transcript
        self._update_video(video)

    def _rate_sentiment(self, video: YtVideo):
        if video.stats.sentiment_rating and not self.overwrite_existing_data:
            title_sentiment_rating = video.stats.sentiment_rating.score_title
            transcript_sentiment_rating = video.stats.sentiment_rating.score_transcript
        else:
            title_sentiment_rating = self.sentiment_rater.rate(video.title).score
            transcript_sentiment_rating = (
                self.sentiment_rater.rate(video.transcript).score
                if video.transcript
                else None
            )

        sentiment_rating = YoutubeVideoSentimentRating(
            model=self.sentiment_rater.model_name,
            score_title=title_sentiment_rating,
            score_transcript=transcript_sentiment_rating,
        )
        video.stats.sentiment_rating = sentiment_rating
        self._update_video(video)
