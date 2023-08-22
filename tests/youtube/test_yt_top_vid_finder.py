import datetime

import pytest
from mockito import any, mock, verify, when

from config_data_provider import get_yt_api_keys
from model.youtube.core import YtVideo, YtVideoStats
from model.youtube.yt_top_vid_finder import YtFinder


@pytest.fixture(scope="module")
def yt_finder() -> YtFinder:
    return YtFinder(get_yt_api_keys())


@pytest.mark.parametrize("max_results,expected_length", [
    (10, 10),
    (5, 5),
])
def test_scrape_top_videos_basic_info(yt_finder, max_results, expected_length):
    vid_list_basic_info_generator = yt_finder.scrape_top_videos_basic_info(
        topic="Bitcoin",
        date_start=datetime.date(2020, 1, 1),
        date_end=datetime.date(2020, 1, 7),
        time_delta=7,
        max_results_per_time_delta=max_results,
    )

    list_of_vid_lists = list(vid_list_basic_info_generator)
    assert len(list_of_vid_lists) == 1
    assert len(list_of_vid_lists[0]) == expected_length
    assert isinstance(list_of_vid_lists[0][0], YtVideo)


def test_scrape_top_videos_basic_info_when_two_time_partitions_should_yield_2_lists(
    yt_finder,
):
    vid_list_basic_info_generator = yt_finder.scrape_top_videos_basic_info(
        topic="Bitcoin",
        date_start=datetime.date(2020, 1, 1),
        date_end=datetime.date(2020, 1, 14),
        time_delta=7,
        max_results_per_time_delta=5,
    )

    list_of_vid_lists = list(vid_list_basic_info_generator)
    assert len(list_of_vid_lists) == 2
    assert len(list_of_vid_lists[0]) == 5
    assert len(list_of_vid_lists[1]) == 5
    assert isinstance(list_of_vid_lists[0][0], YtVideo)
    assert isinstance(list_of_vid_lists[1][0], YtVideo)


def test_scrape_video_stats_never_gonna_give_you_up_should_return_over_1b_views_2m_comments_3half_length(
    yt_finder,
):
    rick_id = "dQw4w9WgXcQ"
    vid = YtVideo(
        video_id=rick_id,
        title="Rick Astley - Never Gonna Give You Up (Video)",
        channel="RickAstleyVEVO",
        date=datetime.datetime(2009, 10, 25, 0, 0),
    )

    stats: YtVideoStats = yt_finder.scrape_video_stats(vid)
    assert stats.views > 1_000_000_000
    assert stats.comments > 2_000_000
    assert 3.5 < stats.length_minutes < 3.7


def test_scrape_top_videos_with_stats_should_yield_list_of_videos_with_stats(yt_finder):
    vid_list_full_info_generator = yt_finder.scrape_top_videos_with_stats(
        topic="Bitcoin",
        date_start=datetime.date(2020, 1, 1),
        date_end=datetime.date(2020, 1, 7),
        time_delta=7,
        max_results_per_time_delta=5,
    )

    list_of_vid_lists = list(vid_list_full_info_generator)
    assert len(list_of_vid_lists) == 1
    assert len(list_of_vid_lists[0]) == 5
    assert isinstance(list_of_vid_lists[0][0], YtVideo)
    assert isinstance(list_of_vid_lists[0][0].stats, YtVideoStats)
    assert list_of_vid_lists[0][0].stats.views > 1


def test_scrape_top_videos_when_quota_reached_should_switch_api_keys_then_raise(
    yt_finder,
):
    mock_api_client = mock()

    # make mock api client throw exception when we call search method on it to simulate
    # the quota limit reached
    when(mock_api_client).search(any()).thenRaise(Exception("quota limit reached"))

    api_keys_number = len(get_yt_api_keys())

    when(yt_finder)._build_client().thenReturn(mock_api_client)
    yt_finder._youtube = yt_finder._build_client()

    with pytest.raises(Exception, match="quota limit reached"):
        list(
            yt_finder.scrape_top_videos_basic_info(
                topic="Bitcoin",
                date_start=datetime.date(2020, 1, 1),
                date_end=datetime.date(2020, 1, 14),
                time_delta=7,
                max_results_per_time_delta=5,
            )
        )

    # make sure the client gets rebuilt number of times equal to number
    # of our api keys
    verify(yt_finder, times=api_keys_number)._build_client()
