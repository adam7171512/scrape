import datetime
import model.factories
from model.data_analysis.youtube_stats_analysis import \
    create_btc_price_sentiment_analysis

if __name__ == "__main__":
    pipeline = model.factories.create_scraping_pipeline()

    # yt data collection

    pipeline.process(
        topic="Bitcoin",
        date_start=datetime.date(2020, 8, 1),
        date_end=datetime.date(2023, 1, 1),
        time_delta=7,
        max_results_per_time_delta=5,
    )

    yt_btc_price_analysis = create_btc_price_sentiment_analysis()
    yt_btc_price_analysis.plot()
