from config_data_provider import (get_config, get_open_ai_api_key,
                                  get_scraper_config, get_yt_api_keys)
from model.persistence.core import IYtVideoRepository
from model.persistence.factory import YtVideoRepositoryFactory
from model.pipeline.batch_pipeline import YtVidScrapingBatchPipeline
from model.pipeline.core import IYtVidScrapingPipeline
from model.pipeline.serial_pipeline import YtVidScrapingSerialPipeline
from model.pipeline.std_pipeline import YtVidScrapingStdPipeline
from model.sentiment_analysis.core import ISentimentRater
from model.sentiment_analysis.sentiment_gpt import GptSentimentRater
from model.sentiment_analysis.sentiment_roberta import RobertaSentimentRater
from model.youtube.core import (IYtStatsScraper, IYtTopVideoFinder,
                                IYtTranscriptScraper)
from model.youtube.sentiment_filler import SentimentFiller
from model.youtube.transcript_filler import TranscriptFiller
from model.youtube.whisper_transcript import WhisperTranscriptExtractor
from model.youtube.yt_audio_downloader import YtAudioDownloader
from model.youtube.yt_transcript_scraper import (ComboYtTranscriptScraper,
                                                 YtDlpTranscriptScraper,
                                                 YtWhisperTranscriptScraper)

config = get_config()


def create_stats_scraper() -> IYtStatsScraper:
    scraper_config = get_scraper_config()
    if scraper_config["stats_scraper"] == "yt-dlp":
        from model.youtube.yt_stats_scraper import YtDlpStatsScraper

        return YtDlpStatsScraper()
    elif scraper_config["stats_scraper"] == "ytapi":
        from model.youtube.yt_stats_scraper import YtApiStatsScraper

        return YtApiStatsScraper()
    else:
        raise Exception("Invalid stats scraper type")


def create_top_video_finder() -> IYtTopVideoFinder:
    stats_scraper = create_stats_scraper()
    from model.youtube.yt_top_vid_finder import YtTopVideoFinder

    api_keys = get_yt_api_keys()
    return YtTopVideoFinder(api_keys, stats_scraper=stats_scraper)


def create_transcript_scraper() -> IYtTranscriptScraper:
    scraper_config = get_scraper_config()
    if scraper_config["transcript_scraper"] == "yt-dlp":
        transcript_scraper = YtDlpTranscriptScraper()
    elif scraper_config["transcript_scraper"] == "whisper":
        whisper = WhisperTranscriptExtractor()
        transcript_scraper = YtWhisperTranscriptScraper(
            whisper,
            YtAudioDownloader(),
        )
    elif scraper_config["transcript_scraper"] == "combo":
        transcript_scraper = ComboYtTranscriptScraper()
    else:
        raise Exception("Invalid transcript scraper type")
    return transcript_scraper


def create_video_repository():
    db_config = config["db"]

    if db_config["repository"] == "mongo":
        repository: IYtVideoRepository = YtVideoRepositoryFactory.mongo_repository(
            db_config["db_name"], db_config["collection_name"]
        )
    else:
        raise Exception("Invalid repository type")

    return repository


def create_sentiment_rater() -> ISentimentRater:
    scraper_config = get_scraper_config()
    if scraper_config["sentiment_rater"] == "roberta":
        return RobertaSentimentRater()
    elif scraper_config["sentiment_rater"] == "gpt":
        return GptSentimentRater(get_open_ai_api_key())
    else:
        raise Exception("Invalid sentiment rater type")


def create_scraping_pipeline() -> IYtVidScrapingPipeline:
    pipeline = config["pipeline"]

    if pipeline == "std":
        return YtVidScrapingStdPipeline(
            create_video_repository(),
            create_top_video_finder(),
            create_transcript_scraper(),
            create_sentiment_rater(),
            config["overwrite_existing_data"],
        )
    elif pipeline == "batch":
        return YtVidScrapingBatchPipeline(
            create_video_repository(),
            create_top_video_finder(),
            create_transcript_scraper(),
            create_sentiment_rater(),
            config["overwrite_existing_data"],
        )
    elif pipeline == "serial":
        return YtVidScrapingSerialPipeline(
            create_video_repository(),
            create_top_video_finder(),
            create_transcript_scraper(),
            create_sentiment_rater(),
        )


def create_transcript_filler() -> TranscriptFiller:
    return TranscriptFiller(create_transcript_scraper(), create_video_repository())


def create_sentiment_filler() -> SentimentFiller:
    return SentimentFiller(
        create_sentiment_rater(),
        create_video_repository(),
        config["overwrite_existing_data"],
    )
