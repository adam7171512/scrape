import re

from model.youtube.core import IYtStatsScraper, YtVideoStats


class YtApiStatsScraper(IYtStatsScraper):
    def __init__(self, yt_client):
        self._yt_client = yt_client

    def scrape_stats(self, video_id: str) -> YtVideoStats:
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

        request = self._yt_client.videos().list(
            part="statistics,contentDetails",
            id=video_id,
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

        return video_stats


class YtDlpStatsScraper(IYtStatsScraper):
    def __init__(self):
        import yt_dlp as yt
        self._yt = yt.YoutubeDL()

    def scrape_stats(self, video_id: str) -> YtVideoStats:
        vid_url = f"https://www.youtube.com/watch?v={video_id}"
        info_ = self._yt.extract_info(vid_url, download=False)

        return YtVideoStats(
            views=int(info_["view_count"]),
            comments=int(info_["comment_count"]),
            likes=int(info_["like_count"]),
            length_minutes=info_["duration"] / 60,
        )
