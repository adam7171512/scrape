from typing import Protocol

from model.data.yt_video import YtVideo
from model.yt_tools.whisper_transcript import WhisperTranscript
from model.yt_tools.yt_audio_downloader import YtAudioDownloader


class IYtTranscriptScraper(Protocol):
    def scrape(self, video: YtVideo) -> str:
        ...

class YtWhisperTranscriptScraper(IYtTranscriptScraper):

    def __init__(self, whisper : WhisperTranscript, yt_audio_downloader: YtAudioDownloader):
        self.whisper = whisper
        self.yt_audio_downloader = yt_audio_downloader

    def scrape(self, video: YtVideo) -> str:
        return self.whisper.transcribe(self.yt_audio_downloader.download(video))

class YtYtDlpTranscriptScraper(IYtTranscriptScraper):

    def __init__(self):
        import yt_dlp as yt
        self.yt = yt.YoutubeDL()

    def scrape_from_url(self, url: str, include_auto_captions: bool = True) -> str | None:
        import requests
        try:
            info_ = self.yt.extract_info(url, download=False)

            # manual captions
            captions = info_.get('subtitles', {}).get('en', None)
            if captions:
                for sub in captions:
                    if sub['ext'] == 'vtt':
                        r = requests.get(sub['url'], allow_redirects=True)
                        return self._process_sub_request(r.text)
            elif include_auto_captions:
                # automatic captions
                captions = info_.get('automatic_captions', {}).get('en', None)
                for sub in captions:
                    if sub['ext'] == 'vtt':
                        r = requests.get(sub['url'], allow_redirects=True)
                        return self._process_sub_request_automatic_captions(r.text)
            else:
                return None
            
        except Exception as e:
            print("Error scraping transcript" + str(e))
            return None

    def scrape(self, video: YtVideo, include_auto_captions: bool = True) -> str:
        return self.scrape_from_url(video.url, include_auto_captions)

    def _process_sub_request(self, req):
        import re
        lines = req.split('\n')

        # pattern for timestamps
        pattern = re.compile(r'^\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}$')

        # find the first line with a timestamp
        for i, line in enumerate(lines):
            if pattern.match(line):
                start_line = i
                break

        # use only the lines starting from the first timestamp
        lines = lines[start_line:]

        # remove lines with timestamps, empty lines, and "&nbsp;"
        lines = [line.strip().replace("&nbsp;", " ") for line in lines if not pattern.match(line) and line.strip()]

        # Join the lines
        text = ' '.join(lines)

        # remove any multiple white spaces
        text = re.sub(' +', ' ', text)

        return text

    def _process_sub_request_automatic_captions(self, text):
        import re
        # pattern for text inside <c>...</c> tags
        pattern = re.compile(r'<c>(.*?)</c>')

        # find all instances of the pattern
        matches = re.findall(pattern, text)

        # join the matches with spaces
        text = ' '.join(matches)

        # remove any multiple white spaces
        text = re.sub(' +', ' ', text)

        return text


