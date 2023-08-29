from typing import Protocol

from model.youtube.core import YtVideo, get_url_for_vid_id, IYtTranscriptScraper
from model.youtube.whisper_transcript import WhisperTranscriptExtractor
from model.youtube.yt_audio_downloader import YtAudioDownloader


class YtWhisperTranscriptScraper(IYtTranscriptScraper):
    """
    Class responsible for extracting video transcript.
    It depends on the whisper transcript extractor and on audio downloader.
    """

    def __init__(
            self, whisper: WhisperTranscriptExtractor, yt_audio_downloader: YtAudioDownloader
    ):
        self._whisper = whisper
        self._yt_audio_downloader = yt_audio_downloader

    def scrape_transcript(self, video_id: str) -> str | None:
        return self._whisper.transcribe(self._yt_audio_downloader.download(video_id))


class YtDlpTranscriptScraper(IYtTranscriptScraper):
    """
    Class responsible for scraping the video subtitles.
    Initializer accepts an auto caption toggle.
    Warning! Sometimes the auto captions are VERY bad and limited
    """

    def __init__(self, include_auto_captions: bool = False):
        self._include_auto_captions = include_auto_captions
        import yt_dlp as yt

        self._yt = yt.YoutubeDL()

    def scrape_transcript(self, video_id: str) -> str | None:
        import requests
        try:
            url_str = get_url_for_vid_id(video_id)
            info_ = self._yt.extract_info(url_str, download=False)

            # manual captions
            captions = info_.get("subtitles", {}).get("en", None)
            if captions:
                for sub in captions:
                    if sub["ext"] == "vtt":
                        response = requests.get(sub["url"], allow_redirects=True)
                        return self._process_sub_request_response(response.text)
            elif self._include_auto_captions:
                # automatic captions
                captions = info_.get("automatic_captions", {}).get("en", None)
                for sub in captions:
                    if sub["ext"] == "vtt":
                        response = requests.get(sub["url"], allow_redirects=True)
                        return self._process_sub_request_response_automatic_captions(response.text)
            else:
                return None
        except Exception as e:
            print("Error scraping transcript" + str(e))
            return None

    def _process_sub_request_response(self, text: str) -> str | None:
        import re

        lines = text.split("\n")

        # pattern for timestamps
        pattern = re.compile(r"^\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}$")

        start_line = None

        for i, line in enumerate(lines):
            if pattern.match(line):
                start_line = i
                break

        # use only the lines starting from the first timestamp
        lines = lines[start_line:] if start_line else []

        # remove lines with timestamps, empty lines, and "&nbsp;"
        lines = [
            line.strip().replace("&nbsp;", " ")
            for line in lines
            if not pattern.match(line) and line.strip()
        ]

        text = " ".join(lines)

        # remove any multiple white spaces
        text = re.sub(" +", " ", text)

        return text if text else None

    def _process_sub_request_response_automatic_captions(self, text: str) -> str | None:
        import re

        # pattern for text inside <c>...</c> tags
        pattern = re.compile(r"<c>(.*?)</c>")

        # find all instances of the pattern
        matches = re.findall(pattern, text)

        # join the matches with spaces
        text = " ".join(matches)

        # remove any multiple white spaces
        text = re.sub(" +", " ", text)

        return text if text else None


class ComboYtTranscriptScraper(IYtTranscriptScraper):
    """
    Class responsible for extracting video transcript.
    It firstly tries to obtain captions using yt-dlp as a cheap method (only manual captions by default),
    if the captions are not available, then it uses whisper extractor.
    """

    def __init__(self, whisper_model: str = "base", length_min: int = 5, auto_captions: bool = False):
        self.scraper = YtWhisperTranscriptScraper(
            WhisperTranscriptExtractor(whisper_model),
            YtAudioDownloader(length_min)
        )

        self.yt_dlp_scraper = YtDlpTranscriptScraper(auto_captions)

    def scrape_transcript(self, video_id: str) -> str | None:
        transcript = self.yt_dlp_scraper.scrape_transcript(video_id)

        if transcript is None:
            transcript = self.scraper.scrape_transcript(video_id)

        return transcript
