import logging
from datetime import date, timedelta

import pandas as pd

logging.basicConfig(level=logging.INFO)


def get_binance_monthly_published_data(
    ticker: str, date_within_month: date, ohlc_interval: str = "15m"
) -> pd.DataFrame:
    date_str = date_within_month.strftime("%Y-%m")
    url = f"https://data.binance.vision/data/spot/monthly/klines/{ticker}/" \
          f"{ohlc_interval}/{ticker}-{ohlc_interval}-{date_str}.zip"
    logging.info(f"getting data from {url}")
    df = pd.read_csv(url, compression="zip", header=0, sep=",", quotechar='"')
    logging.info(f"got data from {url}")
    df.columns = [
        "open_time",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "close_time",
        "quote_asset_volume",
        "number_of_trades",
        "taker_buy_base_asset_volume",
        "taker_buy_quote_asset_volume",
        "ignore",
    ]
    return df


def get_binance_monthly_for_date_range(
    ticker: str, date_start: date, date_end: date, ohlc_interval: str = "15m"
):
    d = date_start
    df_list = []
    df = None
    while d <= date_end:
        logging.info(f"getting data for {d}")
        try:
            df2 = get_binance_monthly_published_data(ticker, d, ohlc_interval)
            df_list.append(df2)
            df = pd.concat(df_list, ignore_index=True)
            logging.info(f"got data for {d}")
        except Exception as e:
            logging.error(f"failed to get data for {d} {e}")
        d += timedelta(days=30)
    logging.info(f"got data for {ticker} from {date_start} to {date_end}")
    return df

