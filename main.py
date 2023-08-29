import datetime

import config_data_provider
from model.pipeline.pipeline_factory import get_scraping_pipeline


if __name__ == "__main__":
    config = config_data_provider.get_config()
    pipeline = get_scraping_pipeline(config)

    # yt data collection

    pipeline.process(
        topic="Bitcoin",
        date_start=datetime.date(2023, 1, 1),
        date_end=datetime.date(2023, 2, 1),
        time_delta=7,
        max_results_per_time_delta=3,
    )
