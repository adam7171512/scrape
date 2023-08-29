from model.youtube.core import YtVideo, IYtTranscriptScraper
from model.youtube.persistence.core import IYtVideoRepository
from model.youtube.persistence.mongo import YtVideoMongoRepository
from model.youtube.whisper_transcript import WhisperTranscriptExtractor
from model.youtube.yt_audio_downloader import YtAudioDownloader
from model.youtube.yt_transcript_scraper import (
    YtWhisperTranscriptScraper,
    YtDlpTranscriptScraper)


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


# Todo: replace fixed urls with config
def create_whisper_transcript_filler(
        db_name, collection_name, model_size: str = "medium"
):
    import pymongo

    client = pymongo.MongoClient("mongodb://localhost:27017")
    db = client[db_name]
    collection = db[collection_name]
    yt_repository = YtVideoMongoRepository(collection)
    whisper_ = WhisperTranscriptExtractor(model=model_size)
    yt_audio_downloader = YtAudioDownloader(length_min=7)
    transcript_scraper = YtWhisperTranscriptScraper(whisper_, yt_audio_downloader)
    return TranscriptFiller(transcript_scraper, yt_repository)


def create_ytdlp_transcript_filler(db_name, collection_name):
    import pymongo

    client = pymongo.MongoClient("mongodb://localhost:27017")
    db = client[db_name]
    collection = db[collection_name]
    yt_repository = YtVideoMongoRepository(collection)
    transcript_scraper = YtDlpTranscriptScraper()
    return TranscriptFiller(transcript_scraper, yt_repository)
