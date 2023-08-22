import datetime
import logging
import re
from typing import Generator

from googleapiclient.discovery import build

from model.youtube.core import YtVideo, YtVideoStats, IYtStatsScraper
from model.youtube.yt_stats_scraper import YtApiStatsScraper


class YtFinder:
    """
    Todo: remove the key handling responsibility from this class
    """
    API_SERViCE_NAME = "youtube"
    API_VERSION = "v3"

    def __init__(self, api_keys: list[str], stat_scraper: IYtStatsScraper):
        self._api_keys = api_keys
        self._api_key_index = 0
        self.stats_scraper = stat_scraper

        self._youtube = None

    def scrape_top_videos_basic_info(
            self,
            topic: str,
            date_start: datetime.date,
            date_end: datetime.date,
            time_delta: int,
            max_results_per_time_delta: int = 10,
            language: str = None,
    ) -> Generator[list[YtVideo], None, None]:
        """
        Returns a generator of lists of videos, where each list is the top videos for a given time delta
        """
        delta = datetime.timedelta(days=time_delta)

        search_from = date_start
        search_to = date_start + delta

        if self._youtube is None:
            self._youtube = build(
                self.API_SERViCE_NAME,
                self.API_VERSION,
                developerKey=self._api_keys[self._api_key_index],
            )

        while search_from <= date_end:

            if search_to > date_end:
                search_to = date_end

            parameters = {
                "part": "snippet",
                "maxResults": max_results_per_time_delta,
                "order": "viewCount",
                "publishedAfter": f"{search_from}T00:00:00Z",
                "publishedBefore": f"{search_to}T23:59:59Z",
                "q": topic,
                "type": "video",
            }

            if language:
                parameters["relevanceLanguage"] = language

            try:
                request = self._youtube.search().list(
                    **parameters,
                )
                response = request.execute()
                items = response.get("items", [])
                search_results = [
                    YtVideo.from_dict(item)
                    for item in items
                    if item.get("id").get("kind") == "youtube#video"
                ]
                yield search_results

            except Exception as e:
                print(f"Exception: {e}")

                # if we hit the quota limit, switch to the next api key
                # if we run out of api keys, throw the exception, log progress and exit

                if self._next_key():
                    continue
                else:
                    logging.log(
                        logging.ERROR,
                        f"Ran out of api keys whilst searching:"
                        f"topic : {topic} , date range : {date_start} - {date_end}"
                        f"on segment from : {search_from} , search_to : {search_to}",
                    )
                    raise e

            search_from += delta
            search_to += delta

    def _next_key(self) -> bool:

        if self._api_key_index >= len(self._api_keys) - 1:
            return False

        self._api_key_index += 1
        self._youtube = build(
            self.API_SERViCE_NAME,
            self.API_VERSION,
            developerKey=self._api_keys[self._api_key_index],
        )

        return True

    def scrape_video_stats(self, video: YtVideo) -> YtVideoStats:
        try:
            return self.stats_scraper.scrape_stats(video.video_id)
        except Exception as e:
            # if we hit the quota limit, switch to the next api key
            # if we run out of api keys, throw the exception, log progress and exit

            if self._next_key():
                self.stats_scraper = YtApiStatsScraper(self._youtube)
                return self.scrape_video_stats(video)
            else:
                raise e

    # returns generator of lists of videos
    def scrape_top_videos_with_stats(
            self,
            topic: str,
            date_start: datetime.date,
            date_end: datetime.date,
            time_delta: int,
            max_results_per_time_delta: int = 10,
            language: str = None,
            stats_lower_limit: int | None = None,
            length_minutes_lower_limit: int | None = None,
    ) -> Generator[list[YtVideo], None, None]:
        for yt_videos in self.scrape_top_videos_basic_info(
                topic,
                date_start,
                date_end,
                time_delta,
                max_results_per_time_delta,
                language,
        ):
            vids = []
            for yt_video in yt_videos:
                yt_video.stats = self.scrape_video_stats(yt_video)

                meets_criteria = True
                if (
                        length_minutes_lower_limit
                        and yt_video.stats.length_minutes < length_minutes_lower_limit
                ):
                    meets_criteria = False

                if stats_lower_limit and yt_video.stats.views < stats_lower_limit:
                    meets_criteria = False

                if meets_criteria:
                    vids.append(yt_video)

            yield vids
