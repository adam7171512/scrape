import os

import yt_dlp as yt

from model.youtube.core import YtVideo, get_url_for_vid_id


class YtAudioDownloader:
    """
    A class to handle downloading of YouTube videos as audio files.
    Initializer accepts optional length_min parameter, to truncate the length of audio files

    Example:
        downloader = YtAudioDownloader(length_min=5)
        path = downloader.download(YtVideo("https://www.youtube.com/watch?v=dQw4w9WgXcQ"))

    Dependencies:
        yt_dlp, ffmpeg
    """
    # download audio only
    params = {
        "format": "bestaudio/best",
        "outtmpl": "%(id)s.%(ext)s",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],
    }

    def __init__(self, length_min: int = None):
        self._length_min = length_min
        self._ytdl = yt.YoutubeDL(self.params)
        self._downloaded_files = []

    # returns path to downloaded file
    def download(self, video_id: str) -> str:
        url_str = get_url_for_vid_id(video_id)
        print(f"downloading {url_str}")
        self._ytdl.download([url_str])

        # if short, then cut the audio to first 5 minutes
        if self._length_min:
            l_min = str(self._length_min).zfill(2)
            os.system(
                f"ffmpeg -i ./{video_id}.wav -ss 00:00:00 -to 00:{l_min}:00 -c copy ./{video_id}_short.wav"
            )
            os.remove(f"./{video_id}.wav")
            os.rename(f"./{video_id}_short.wav", f"./{video_id}.wav")

        self._downloaded_files.append(f"{video_id}.wav")

        # full path :
        path = f"{os.getcwd()}/{video_id}.wav"
        print(path)
        return path
