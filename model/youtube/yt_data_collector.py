from datetime import datetime

from model.youtube.core import IYtTranscriptScraper
from model.persistence import IYtVideoRepository
from model.youtube.yt_top_vid_finder import YtTopVideoFinder


class YtDataCollector:
    """
    Facade-like class responsible for scraping and persisting the data
    """
    def __init__(
            self,
            repository: IYtVideoRepository,
            vid_finder: YtTopVideoFinder,
            transcript_scraper: IYtTranscriptScraper | None = None,
    ):
        self.repository = repository
        self.vid_finder = vid_finder
        self.transcript_scraper = transcript_scraper

    def collect_data(
        self,
        topic: str,
        date_start: datetime.date,
        date_end: datetime.date,
        time_delta: int,
        max_results_per_time_delta: int = 10,
        language: str = None,
        stats_lower_limit: int | None = None,
        length_minutes_lower_limit: int | None = None,
    ):
        vids = self.vid_finder.scrape_top_videos_with_stats(
            topic=topic,
            date_start=date_start,
            date_end=date_end,
            time_delta=time_delta,
            max_results_per_time_delta=max_results_per_time_delta,
            language=language,
            stats_lower_limit=stats_lower_limit,
            length_minutes_lower_limit=length_minutes_lower_limit,
        )

        for video_batch in vids:
            for video in video_batch:

                if self.transcript_scraper:
                    transcript = self.transcript_scraper.scrape_transcript(video.video_id)
                    video.transcript = transcript

                self.repository.add_if_doesnt_exist(video)
