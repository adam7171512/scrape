from typing import Protocol

from model.youtube.core import YtVideo, get_url_for_vid_id
from model.youtube.whisper_transcript import WhisperTranscript
from model.youtube.yt_audio_downloader import YtAudioDownloader


class IYtTranscriptScraper(Protocol):

    def scrape_transcript(self, video_id: str) -> str | None:
        ...


class YtWhisperTranscriptScraper(IYtTranscriptScraper):
    def __init__(
        self, whisper: WhisperTranscript, yt_audio_downloader: YtAudioDownloader
    ):
        self._whisper = whisper
        self._yt_audio_downloader = yt_audio_downloader

    def scrape_transcript(self, video_id: str) -> str | None:
        return self._whisper.transcribe(self._yt_audio_downloader.download(video_id))


class YtYtDlpTranscriptScraper(IYtTranscriptScraper):
    def __init__(self, include_auto_captions: bool = True):
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
