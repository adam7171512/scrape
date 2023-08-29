from model.persistence.core import IYtVideoRepository
from model.persistence.factory import YtVideoRepositoryFactory
from model.persistence.mongo import YtVideoMongoRepository
from model.youtube.core import YtVideo, IYtTranscriptScraper
from model.youtube.whisper_transcript import WhisperTranscriptExtractor
from model.youtube.yt_audio_downloader import YtAudioDownloader
from model.youtube.yt_transcript_scraper import (
    YtWhisperTranscriptScraper,
    YtDlpTranscriptScraper, ComboYtTranscriptScraper)


class TranscriptFiller:
    """
    Class responsible for filling out missing transcript data for videos in repository

    As the transcript grabbing process can be time-consuming, especially when based on audio processing
    and text extraction using ml model, it's often better to do this process separately.
    """

    def __init__(
            self,
            yt_transcript_scraper: IYtTranscriptScraper,
            yt_repository: IYtVideoRepository,
    ):
        self.yt_transcript_scraper = yt_transcript_scraper
        self.yt_repository = yt_repository

    def fill_transcript(self, video: YtVideo) -> None:
        text = self.yt_transcript_scraper.scrape_transcript(video.video_id)
        video.transcript = text
        self.yt_repository.update_if_exists(video)

    def fill_missing_transcripts(self):
        for vid in self.yt_repository.get_all_videos():
            if not vid.transcript:
                self.fill_transcript(vid)


def create_transcript_filler(config: dict):
    scraper_config = config["scraper"]
    db_config = config["db"]

    if db_config["repository"] == "mongo":
        repository: IYtVideoRepository = YtVideoRepositoryFactory.mongo_repository(
            db_config["db_name"], db_config["collection_name"]
        )
    else:
        raise Exception("Invalid repository type")
    if scraper_config["transcript_scraper"] == "combo":
        transcript_scraper = ComboYtTranscriptScraper()
    elif scraper_config["transcript_scraper"] == "whisper":
        whisper = WhisperTranscriptExtractor()
        transcript_scraper = YtWhisperTranscriptScraper(
            whisper,
            YtAudioDownloader(),
        )
    elif scraper_config["transcript_scraper"] == "yt-dlp":
        transcript_scraper = YtDlpTranscriptScraper()
    else:
        raise Exception("Invalid transcript scraper type")

    return TranscriptFiller(transcript_scraper, repository)

