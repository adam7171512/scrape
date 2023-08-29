import datetime
import logging

from model.sentiment_analysis.core import ISentimentRater
from model.youtube.core import YtVideo, YoutubeVideoSentimentRating
from model.persistence import IYtVideoRepository
from model.youtube.processing.core import IYtVidScrapingProcessor
from model.youtube.yt_top_vid_finder import YtTopVideoFinder
from model.youtube.yt_transcript_scraper import IYtTranscriptScraper


class YtVidScrapingBatchProcessor(IYtVidScrapingProcessor):
    """
    This class is responsible for conducting video search on particular topic,
    scraping the video's stats, transcript, and rating the video's sentiment.
    Then it saves the data to the database using repository.

    The processing is done in a batch manner, meaning that each pipeline step
    is performed on batch of videos (and after each step they get saved/updated in the database).
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

        for video_batch in videos_list_generator:
            self._process_video_batch(video_batch)

    # todo: refactor this to use batch operations

    def _process_video_batch(self, videos: list[YtVideo]):
        vids = self._add_videos_to_database(videos)
        self.scrape_transcripts(vids)
        self.rate_sentiments(vids)

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

    def _update_videos_in_database(self, videos: list[YtVideo]):
        for video in videos:
            self._update_video(video)

    def scrape_transcripts(self, videos: list[YtVideo]):
        for video in videos:
            transcript = video.transcript
            if transcript is None:
                transcript = self.transcript_scraper.scrape_transcript(video.video_id)

            video.transcript = transcript
        self._update_videos_in_database(videos)

    def rate_sentiments(self, videos: list[YtVideo]):
        for video in videos:
            transcript = video.transcript

            # todo: check if the videos have ratings already

            title_sentiment_rating = None
            transcript_sentiment_rating = None

            if video.stats.sentiment_rating is not None:
                title_sentiment_rating = video.stats.sentiment_rating.score_title
                transcript_sentiment_rating = video.stats.sentiment_rating.score_transcript

            if title_sentiment_rating is None:
                title_sentiment_rating = self.sentiment_rater.rate(video.title).score
            if transcript and transcript_sentiment_rating is None:
                transcript_sentiment_rating = self.sentiment_rater.rate(transcript).score
            elif not transcript:
                logging.log(logging.ERROR, f"Video {video.video_id} has no transcript.")

            sentiment_rating = YoutubeVideoSentimentRating(
                model=self.sentiment_rater.model_name,
                score_title=title_sentiment_rating,
                score_transcript=transcript_sentiment_rating,
            )
            video.stats.sentiment_rating = sentiment_rating
        self._update_videos_in_database(videos)

    def _save_video(self, video: YtVideo):
        added = self.repository.add_if_doesnt_exist(video)

        if not added:
            logging.log(logging.ERROR, f"Video {video.video_id} already exists in the database.")

    def _update_video(self, video: YtVideo):
        updated = self.repository.update_if_exists(video)

        if not updated:
            logging.log(logging.ERROR, f"Video {video.video_id} doesn't exist in the database.")
