from config_data_provider import get_scraper_config, get_open_ai_api_key, get_yt_api_keys, get_db_config
from model.persistence.core import IYtVideoRepository
from model.persistence.factory import YtVideoRepositoryFactory
from model.sentiment_analysis.sentiment_gpt import GptSentimentRater
from model.sentiment_analysis.sentiment_roberta import RobertaSentimentRater
from model.pipeline.batch_pipeline import YtVidScrapingBatchPipeline
from model.pipeline.core import IYtVidScrapingPipeline
from model.pipeline.serial_pipeline import YtVidScrapingSerialPipeline
from model.pipeline.std_pipeline import YtVidScrapingStdPipeline
from model.youtube.whisper_transcript import WhisperTranscriptExtractor
from model.youtube.yt_audio_downloader import YtAudioDownloader
from model.youtube.yt_stats_scraper import YtDlpStatsScraper, YtApiStatsScraper
from model.youtube.yt_top_vid_finder import YtTopVideoFinder
from model.youtube.yt_transcript_scraper import YtWhisperTranscriptScraper, YtDlpTranscriptScraper, \
    ComboYtTranscriptScraper


def get_scraping_pipeline(config: dict) -> IYtVidScrapingPipeline:
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
    # Todo: change to match and consider removing whisper extractor injection from whisper scraper
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

    yt_finder = YtTopVideoFinder(get_yt_api_keys(), stats_scraper=stats_scraper)

    if scraper_config["pipeline"] == "std":
        return YtVidScrapingStdPipeline(
            repository,
            yt_finder,
            transcript_scraper,
            sentiment_rater,
            overwrite_existing_data,
        )
    elif scraper_config["pipeline"] == "serial":
        return YtVidScrapingSerialPipeline(
            repository,
            yt_finder,
            transcript_scraper,
            sentiment_rater,
        )
    elif scraper_config["pipeline"] == "batch":
        return YtVidScrapingBatchPipeline(
            repository,
            yt_finder,
            transcript_scraper,
            sentiment_rater,
            overwrite_existing_data,
        )
    else:
        raise Exception("Invalid pipeline type")