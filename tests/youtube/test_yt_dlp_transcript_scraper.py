import datetime

import pytest

from model.youtube.core import IYtTranscriptScraper, YtVideo
from model.youtube.yt_transcript_scraper import YtDlpTranscriptScraper


@pytest.fixture(scope="module")
def yt_transcript_scraper() -> IYtTranscriptScraper:
    return YtDlpTranscriptScraper(include_auto_captions=True)


def test_scrape_transcript_never_gonna_give_you_up(
    yt_transcript_scraper,
):
    rick_id = "dQw4w9WgXcQ"
    vid = YtVideo(
        video_id=rick_id,
        title="Rick Astley - Never Gonna Give You Up (Video)",
        channel="RickAstleyVEVO",
        date=datetime.datetime(2009, 10, 25, 0, 0),
    )

    transcript = yt_transcript_scraper.scrape_transcript(rick_id)

    # suprisingly, yt does not proper full subs for this vid, auto captions are very limited
    assert "just wanna tell you how I'm feeling" in transcript
