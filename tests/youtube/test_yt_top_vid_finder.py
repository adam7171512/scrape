import datetime

from model.youtube.yt_top_vid_finder import YtFinder, get_api_keys
import pytest
@pytest.fixture(scope="module")
def yt_finder() -> YtFinder:
    return YtFinder(get_api_keys())

def test_yt_finder(yt_finder):
    vid_list = list(yt_finder.scrape_top_videos_basic_info(
        topic="Bitcoin",
        date_start=datetime.date(2020, 1, 1),
        date_end=datetime.date(2020, 1, 2),
        time_delta=1,
        max_results_per_time_delta=10,
    ))

    assert len(vid_list) == 10
