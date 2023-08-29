import datetime
import logging

from model.persistence.core import IYtVideoRepository
from model.sentiment_analysis.core import ISentimentRater
from model.youtube.core import YtVideo
from model.youtube.processing.core import IYtVidScrapingProcessor
from model.youtube.yt_top_vid_finder import YtTopVideoFinder
from model.youtube.yt_transcript_scraper import IYtTranscriptScraper


class YtVidScrapingStdProcessor(IYtVidScrapingProcessor):
    """
    This class is responsible for conducting video search on particular topic,
    scraping the video's stats, transcript, and rating the video's sentiment.
    Then it saves the data to the database using repository.

    This implementation follows the pipeline:
    1. Find the videos and their stats
    2. Scrape the transcript
    3. Analyse the sentiment and update the sentiment stats
    """

    def __init__(self,
                 repository: IYtVideoRepository,
                 yt_finder: YtTopVideoFinder,
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

        processed = []

        for video_batch in videos_list_generator:
            processed.extend(self._add_videos_to_database(video_batch))

        transcript_scraped = []

        for video in processed:
            video.transcript = self.transcript_scraper.scrape_transcript(video.video_id)
            # after grabbing the transcript, update one by one not to lose progress in case of failure
            self._update_video(video)
            transcript_scraped.append(video)

        for video in transcript_scraped:
            video.stats.sentiment_rating.score_title = self.sentiment_rater.rate(video.title)
            video.stats.sentiment_rating.score_transcript = self.sentiment_rater.rate(video.transcript)
            self._update_video(video)

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
            logging.log(logging.ERROR, f"Video {video.video_id} already exists in the database.")

    def _update_video(self, video: YtVideo):
        updated = self.repository.update_if_exists(video)

        if not updated:
            logging.log(logging.ERROR, f"Video {video.video_id} doesn't exist in the database.")
