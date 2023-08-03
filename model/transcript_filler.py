from model.data.yt_video import YtVideo
from model.yt_tools.whisper_transcript import WhisperTranscript
from model.yt_tools.yt_audio_downloader import YtAudioDownloader
from model.yt_tools.yt_mongo_repository import YtMongoRepository
from model.yt_tools.yt_transcript_scraper import IYtTranscriptScraper, YtWhisperTranscriptScraper, \
    YtYtDlpTranscriptScraper


class TranscriptFiller:

    def __init__(self, yt_transcript_scraper: IYtTranscriptScraper, yt_repository: YtMongoRepository):
        self.yt_transcript_scraper = yt_transcript_scraper
        self.yt_repository = yt_repository

    def fill_transcript(self, video: YtVideo) -> None:
        text = self.yt_transcript_scraper.scrape(video)
        video.transcript = text
        self.yt_repository.update_if_exists(video)

    def fill_missing_transcripts(self):
        for vid in self.yt_repository.find_all():
            if not vid.transcript:
                self.fill_transcript(vid)


def create_whisper_transcript_filler(db_name, collection_name, model_size: str = "medium"):
    import pymongo
    client = pymongo.MongoClient("mongodb://localhost:27017")
    db = client[db_name]
    collection = db[collection_name]
    yt_repository = YtMongoRepository(collection)
    whisper_ = WhisperTranscript(model=model_size)
    yt_audio_downloader = YtAudioDownloader(length_min=7)
    transcript_scraper = YtWhisperTranscriptScraper(whisper_, yt_audio_downloader)
    return TranscriptFiller(transcript_scraper, yt_repository)


def create_ytdlp_transcript_filler(db_name, collection_name):
    import pymongo
    client = pymongo.MongoClient("mongodb://localhost:27017")
    db = client[db_name]
    collection = db[collection_name]
    yt_repository = YtMongoRepository(collection)
    transcript_scraper = YtYtDlpTranscriptScraper()
    return TranscriptFiller(transcript_scraper, yt_repository)
