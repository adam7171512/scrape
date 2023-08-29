from model.pipeline.pipeline_factory import get_scraper_pipeline
from model.pipeline.std_pipeline import YtVidScrapingStdPipeline


def test_get_scraper_pipeline():

    config = {
        "api": {
            "yt_data_api_keys": ["mock"],
        },
        "db": {
            "repository": "mongo",
            "mongo_db_url": "mongodb://localhost:27017",
            "db_name": "mock",
            "collection_name": "mock"
        },
        "scraper": {
            "transcript_scraper": "combo",
            "stats_scraper": "yt-dlp",
            "pipeline": "std",
            "sentiment_rater": "roberta",
            "overwrite_existing_data": False,
        }
    }
    scraping_pipeline = get_scraper_pipeline(config)

    assert isinstance(scraping_pipeline, YtVidScrapingStdPipeline)
