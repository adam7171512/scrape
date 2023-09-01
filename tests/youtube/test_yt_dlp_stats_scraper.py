import datetime

import pytest

from model.youtube.core import IYtStatsScraper, YtVideo, YtVideoStats
from model.youtube.yt_stats_scraper import YtDlpStatsScraper


@pytest.fixture(scope="module")
def yt_stat_scraper() -> IYtStatsScraper:
    return YtDlpStatsScraper()


def test_scrape_video_stats_never_gonna_give_you_up_should_return_over_1b_views_2m_comments_3half_length(
    yt_stat_scraper,
):
    rick_id = "dQw4w9WgXcQ"
    vid = YtVideo(
        video_id=rick_id,
        title="Rick Astley - Never Gonna Give You Up (Video)",
        channel="RickAstleyVEVO",
        date=datetime.datetime(2009, 10, 25, 0, 0),
    )

    stats: YtVideoStats = yt_stat_scraper.scrape_stats(vid.video_id)
    assert stats.views > 1_000_000_000
    assert stats.comments > 2_000_000
    assert 3.5 < stats.length_minutes < 3.7
