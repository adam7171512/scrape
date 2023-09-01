import datetime

import pytest

from model.youtube.core import IYtTranscriptScraper, YtVideo
from model.youtube.whisper_transcript import WhisperTranscriptExtractor
from model.youtube.yt_audio_downloader import YtAudioDownloader
from model.youtube.yt_transcript_scraper import YtWhisperTranscriptScraper


@pytest.fixture(scope="module")
def yt_transcript_scraper() -> IYtTranscriptScraper:
    whisper = WhisperTranscriptExtractor()
    yt_audio_downloader = YtAudioDownloader(length_min=5)
    return YtWhisperTranscriptScraper(whisper, yt_audio_downloader)


def test_scrape_transcript_never_gonna_give_you_up(
    yt_transcript_scraper,
):
    rick_id = "dQw4w9WgXcQ"

    transcript = yt_transcript_scraper.scrape_transcript(rick_id)
    print(transcript)

    assert "Never gonna give you up" in transcript
