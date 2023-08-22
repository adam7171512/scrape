from config_data_provider import get_scraper_config, get_open_ai_api_key, get_yt_api_keys, get_db_config
from model.sentiment_analysis.sentiment_gpt import GptSentimentRater
from model.sentiment_analysis.sentiment_roberta import RobertaSentimentRater
from model.youtube.persistence.core import IYtVideoRepository
from model.youtube.persistence.factory import YtRepositoryFactory
from model.youtube.processing.batch_processor import YtVidScrapingBatchProcessor
from model.youtube.processing.core import IYtVidScrapingProcessor
from model.youtube.processing.serial_processor import YtVidScrapingSerialProcessor
from model.youtube.whisper_transcript import WhisperTranscript
from model.youtube.yt_audio_downloader import YtAudioDownloader
from model.youtube.yt_stats_scraper import YtDlpStatsScraper, YtApiStatsScraper
from model.youtube.yt_top_vid_finder import YtFinder
from model.youtube.yt_transcript_scraper import YtWhisperTranscriptScraper, YtYtDlpTranscriptScraper

scraper_config = get_scraper_config()
db_config = get_db_config(scraper_config["repository"])


def get_scraper_processor() -> IYtVidScrapingProcessor:

    if scraper_config["repository"] == "mongo":
        repository: IYtVideoRepository = YtRepositoryFactory.mongo_repository(
            db_config["db_name"], db_config["collection_name"]
        )
    else:
        raise Exception("Invalid repository type")

    if scraper_config["transcript_scraper"] == "whisper":
        whisper = WhisperTranscript()
        transcript_scraper = YtWhisperTranscriptScraper(
            whisper,
            YtAudioDownloader(),
        )
    elif scraper_config["transcript_scraper"] == "yt-dlp":
        transcript_scraper = YtYtDlpTranscriptScraper()
    else:
        raise Exception("Invalid transcript scraper type")

    if scraper_config["sentiment_rater"] == "roberta":
        sentiment_rater = RobertaSentimentRater()
    elif scraper_config["sentiment_rater"] == "gpt":
        sentiment_rater = GptSentimentRater(
            get_open_ai_api_key()
        )
    else:
        raise Exception("Invalid sentiment rater type")

    overwrite_existing_data = scraper_config["overwrite_existing_data"]

    stats_scraper = None
    if scraper_config["stats_scraper"] == "yt-dlp":
        stats_scraper = YtDlpStatsScraper()
    elif scraper_config["stats_scraper"] == "ytapi":
        stats_scraper = YtApiStatsScraper()

    yt_finder = YtFinder(get_yt_api_keys(), stats_scraper=stats_scraper)

    if scraper_config["pipeline"] == "serial":
        return YtVidScrapingSerialProcessor(
            repository,
            yt_finder,
            transcript_scraper,
            sentiment_rater,
        )
    elif scraper_config["pipeline"] == "batch":
        return YtVidScrapingBatchProcessor(
            repository,
            yt_finder,
            transcript_scraper,
            sentiment_rater,
            overwrite_existing_data,
        )
    else:
        raise Exception("Invalid pipeline type")
