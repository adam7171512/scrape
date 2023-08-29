import datetime
import logging
from typing import Any, Generator

from googleapiclient.discovery import build

from model.youtube.core import IYtStatsScraper, YtVideo, YtVideoStats
from model.youtube.yt_stats_scraper import YtApiStatsScraper


class YtTopVideoFinder:
    """
       A class that finds top yt videos and their stats for specified parameters.
       Class handles multiple yt data api keys and after exhausting quota jumps to next one.

       Initializer accepts list of api keys and optional stats scraper dependency.
       If stats scraper is not provided, it creates the stats scraper using yt data api, using keys
       """

    # Todo: remove the key handling responsibility from this class

    API_SERVICE_NAME = "youtube"
    API_VERSION = "v3"

    def __init__(self, api_keys: list[str], stats_scraper: IYtStatsScraper = None):
        self._api_keys = api_keys
        self._api_key_index = 0

        self._youtube = self._build_client()
        self._stats_scraper = stats_scraper

        if stats_scraper is None:
            self._stats_scraper = YtApiStatsScraper()
            self._stats_scraper.set_yt_api_client(self._youtube)

    def _build_client(self) -> Any:
        api_key = self._api_keys[self._api_key_index]
        logging.log(
            logging.WARNING,
            f"Rebuilding the api client, key: {api_key}. "
            f"Current key index: {self._api_key_index}",
        )

        return build(
            self.API_SERVICE_NAME,
            self.API_VERSION,
            developerKey=api_key,
        )

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

        while search_from <= date_end:
            if search_to > date_end:
                search_to = date_end

            logging.log(
                logging.DEBUG,
                f"Attempting youtube api search : \n"
                f"topic: {topic}, from: {search_from} , to: {search_to}",
            )

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
                    raise Exception("quota limit reached")

            search_from += delta
            search_to += delta

    def _next_key(self) -> bool:
        logging.log(
            logging.WARNING,
            f"Switching the api key, as the {self._api_key_index} "
            f"key quota has been reached",
        )

        if self._api_key_index >= len(self._api_keys) - 1:
            logging.log(
                logging.ERROR,
                f"All api keys used. Current index: {self._api_key_index}."
                f" Cant build new client",
            )

            return False

        self._api_key_index += 1
        self._youtube = self._build_client()

        return True

    def scrape_video_stats(self, video: YtVideo) -> YtVideoStats:
        logging.log(
            logging.DEBUG, f"Attempting stats scraping for video, id : {video.video_id}"
        )

        try:
            return self._stats_scraper.scrape_stats(video.video_id)
        except Exception as e:
            # if we hit the quota limit, switch to the next api key
            # if we run out of api keys, throw the exception, log progress and exit

            if isinstance(self._stats_scraper, YtApiStatsScraper) and self._next_key():
                self._stats_scraper.set_yt_api_client(self._youtube)
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
