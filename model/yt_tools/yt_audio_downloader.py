import datetime
import os

import yt_dlp as yt

from model.data.yt_video import YtVideo


class YtAudioDownloader:
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
        self.length_min = length_min
        self.ytdl = yt.YoutubeDL(self.params)
        self.downloaded_files = []

    # returns path to downloaded file
    def download(self, video: YtVideo) -> str:
        url = video.url
        print(f"downloading {url}")
        self.ytdl.download([url])

        # if short, then cut the audio to first 5 minutes
        if self.length_min:
            l_min = str(self.length_min).zfill(2)
            os.system(
                f"ffmpeg -i ./{video.video_id}.wav -ss 00:00:00 -to 00:{l_min}:00 -c copy ./{video.video_id}_short.wav"
            )
            os.remove(f"./{video.video_id}.wav")
            os.rename(f"./{video.video_id}_short.wav", f"./{video.video_id}.wav")

        self.downloaded_files.append(f"{video.video_id}.wav")

        # full path :
        path = f"{os.getcwd()}/{video.video_id}.wav"
        print(path)
        return path
