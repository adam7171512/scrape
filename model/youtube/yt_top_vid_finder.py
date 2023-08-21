import datetime
import logging
import re
from typing import Generator

from googleapiclient.discovery import build

from model.youtube.core import YtVideo, YtVideoStats


def get_api_keys() -> list[str]:
    import toml
    config = toml.load("../../config.toml")
    api_keys = config["api"]["yt_data_api_keys"]
    return api_keys


class YtFinder:
    API_SERViCE_NAME = "youtube"
    API_VERSION = "v3"

    def __init__(self, api_keys: list[str]):
        self.api_keys = api_keys
        self.api_key_index = 0

        self.youtube = None

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

        self.youtube = build(
            self.API_SERViCE_NAME,
            self.API_VERSION,
            developerKey=self.api_keys[self.api_key_index],
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
                request = self.youtube.search().list(
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

                if self.api_key_index >= len(self.api_keys) - 1:
                    logging.log(
                        logging.ERROR,
                        f"Ran out of api keys whilst searching:"
                        f"topic : {topic} , date range : {date_start} - {date_end}"
                        f"on segment from : {search_from} , search_to : {search_to}",
                    )
                    raise e
                self.api_key_index += 1
                self.youtube = build(
                    self.API_SERViCE_NAME,
                    self.API_VERSION,
                    developerKey=self.api_keys[self.api_key_index],
                )
                continue

            search_from += delta
            search_to += delta

    def scrape_video_stats(self, video: YtVideo):
        # Todo: consider changing param to video_id

        video_stats = None

        def _get_duration_in_minutes(duration):
            duration_regex = re.compile(
                r"PT((?P<hours>\d+)H)?((?P<minutes>\d+)M)?((?P<seconds>\d+)S)?"
            )
            matches = duration_regex.match(duration)
            if not matches:
                return 0
            hours = int(matches.group("hours")) if matches.group("hours") else 0
            minutes = int(matches.group("minutes")) if matches.group("minutes") else 0
            seconds = int(matches.group("seconds")) if matches.group("seconds") else 0
            total_minutes = hours * 60 + minutes + seconds / 60.0
            return total_minutes

        if self.youtube is None:
            self.youtube = build(
                self.API_SERViCE_NAME,
                self.API_VERSION,
                developerKey=self.api_keys[self.api_key_index],
            )

        try:
            request = self.youtube.videos().list(
                part="statistics,contentDetails",
                id=video.video_id,
            )
            response = request.execute()
            items = response.get("items", [])
            if len(items) > 0:
                video_stats = YtVideoStats(
                    views=int(items[0].get("statistics").get("viewCount", 0)),
                    comments=int(items[0].get("statistics").get("commentCount", 0)),
                    likes=int(items[0].get("statistics").get("likeCount", 0)),
                    length_minutes=_get_duration_in_minutes(
                        items[0].get("contentDetails").get("duration")
                    ),
                )
        except Exception as e:
            # if we hit the quota limit, switch to the next api key
            # if we run out of api keys, throw the exception, log progress and exit

            if self.api_key_index > len(self.api_keys) - 1:
                logging.log(
                    logging.ERROR,
                    f"Ran out of api keys whilst searching stats:"
                    f"video : {video.video_id} , channel : {video.channel}",
                )
                raise e

            self.api_key_index += 1
            self.youtube = build(
                self.API_SERViCE_NAME,
                self.API_VERSION,
                developerKey=self.api_keys[self.api_key_index],
            )
            return self.scrape_video_stats(video)

        return video_stats

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
    ):
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
