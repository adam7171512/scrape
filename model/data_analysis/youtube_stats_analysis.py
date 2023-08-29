from model.persistence.core import IYtVideoRepository
import pandas as pd
from config_data_provider import get_config
from model.persistence.factory import YtVideoRepositoryFactory


class BtcYoutubeSentimentAnalysis:

    def __init__(self, repository: IYtVideoRepository, btc_price_csv_path: str):
        self.repository = repository
        self.btc_price_csv_path = btc_price_csv_path

    def analyse(self) -> pd.DataFrame:

        def weight_decay(age_weeks):
            if age_weeks <= 4:
                return 0.9 ** age_weeks
            else:
                return 0.6

        df = self._prepare_df()
        cutoff_date = df["date"].max()
        df["video_age_weeks"] = (cutoff_date - df["date"]).dt.days / 7

        df["weight"] = df["video_age_weeks"].apply(weight_decay)
        df["views"] = df["views"] * df["weight"]
        df["likes"] = df["likes"] * df["weight"]
        df["comments"] = df["comments"] * df["weight"]

        df["sentiment_avg"] = df.apply(self._calc_avg_sentiment, axis=1)
        df["sent_impact"] = df["views"] * df["sentiment_avg"] * 0.001

        df = df.sort_values(by=["date"])

        # resample by week, summing impact, views, likes, comments
        df = df.set_index("date")
        df = df.resample("W").sum()

        # calculate exponential moving averages for stats, decay = 0.2 per week
        df["views"] = df["views"].ewm(alpha=0.2).mean()
        df["likes"] = df["likes"].ewm(alpha=0.2).mean()
        df["comments"] = df["comments"].ewm(alpha=0.2).mean()
        df["sent_ema"] = df["sent_impact"].ewm(alpha=0.2).mean()

        df = df.loc[:, ["views", "sent_ema"]]

        btc_usd = self._prepare_btc_df()

        df = df.join(btc_usd, how="inner")

        return df

    def _calc_avg_sentiment(self, row):
        if pd.isnull(row["title_sentiment"]) and pd.isnull(row["transcript_sentiment"]):
            return 0
        elif pd.isnull(row["transcript_sentiment"]):
            return row["title_sentiment"]
        elif pd.isnull(row["title_sentiment"]):
            return row["transcript_sentiment"]
        else:
            return (row["title_sentiment"] + row["transcript_sentiment"]) / 2

    def _prepare_df(self):
        vids = self.repository.get_all_videos()
        vids = [
            {
                "video_id": v.video_id,
                "title": v.title,
                "date": v.date,
                "views": v.stats.views,
                "likes": v.stats.likes,
                "comments": v.stats.comments,
                "length_minutes": v.stats.length_minutes,
                "title_sentiment": v.stats.sentiment_rating.score_title,
                "transcript_sentiment": v.stats.sentiment_rating.score_transcript,
            }
            for v in vids
        ]

        return pd.DataFrame(vids)

    def _prepare_btc_df(self):
        btc_usd = pd.read_csv(self.btc_price_csv_path)
        btc_usd["date"] = pd.to_datetime(btc_usd["date"])
        btc_usd["mean"] = btc_usd[["open", "close"]].mean(axis=1)
        btc_usd = btc_usd.set_index("date")
        btc_usd = btc_usd.loc[:, ["mean"]]
        btc_usd = btc_usd.rename(columns={"mean": "btc_usd"})

        return btc_usd

    def plot(self):
        import matplotlib.pyplot as plt
        df = self.analyse()

        fig, ax1 = plt.subplots(figsize=(15, 10))

        color = "tab:red"
        ax1.set_xlabel("date")
        ax1.set_ylabel("btc_usd", color=color)
        ax1.plot(df.index, df["btc_usd"], color=color)
        ax1.tick_params(axis="y", labelcolor=color)

        ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
        ax2.set_ylabel(
            "sentiment ema", color="tab:blue"
        )  # we already handled the x-label with ax1
        ax2.bar(df.index, df["sent_ema"], color="tab:blue")
        # make bars wider
        for patch in ax2.patches:
            patch.set_width(7)

        ax2.tick_params(axis="y", labelcolor="tab:blue")

        plt.show(block=True)


def create_btc_price_sentiment_analysis():
    config = get_config()
    repo = YtVideoRepositoryFactory.mongo_repository(
        config["db"]["db_name"],
        config["db"]["collection_name"]
    )
    return BtcYoutubeSentimentAnalysis(repo, config["misc"]["btc_price_csv_path"])
