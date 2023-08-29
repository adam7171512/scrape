import datetime

from model.youtube.processing.pipeline_factory import get_scraper_processor


def test_get_scraper_processor():
    scraper_processor = get_scraper_processor()
    assert scraper_processor is not None

    scraper_processor.process(
        "Bitcoin",
        datetime.date(2021, 1, 1),
        datetime.date(2021, 1, 2),
        1,
        10,
    )
