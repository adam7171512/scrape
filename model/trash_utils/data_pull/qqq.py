"https://api.polygon.io/v2/aggs/ticker/QQQ/range/1/minute/2023-01-01/2023-02-01?adjusted=true&sort=asc&limit=50000&apiKey=uP_Wh9PpaphGqy1ZMOHgR10dC3jcC2cY"
import datetime
import json
import time

import requests
from pydantic import BaseModel


# date format YYYY-MM-DD
def get_stock_for_month(date: datetime.date, ticker):
    date_str = date.strftime("%Y-%m-%d")
    next_month = date + datetime.timedelta(days=32)
    next_month = next_month.strftime("%Y-%m-%d")

    print(date_str)
    print(next_month)
    resp = requests.get(
        f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/minute/{date_str}/{next_month}?adjusted=true&sort=asc&limit=50000&apiKey=uP_Wh9PpaphGqy1ZMOHgR10dC3jcC2cY"
    )
    return resp.json()


import pymongo

client = pymongo.MongoClient("mongodb://localhost:27017")
db = client["stocks"]
collection = db["TSLA"]


def get_stock_data_date_range(
    ticker: str, date_start: datetime.date, date_end: datetime.date
):
    d = date_start
    while d <= date_end:
        results = get_stock_for_month(d, ticker).get("results")
        collection.insert_many(results)
        d = d + datetime.timedelta(days=30)
        time.sleep(15)


get_stock_data_date_range("TSLA", datetime.date(2022, 1, 1), datetime.date(2023, 7, 21))
