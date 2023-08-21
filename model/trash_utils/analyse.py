import pandas as pd
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["yt_new"]
collection = db["bitcoin"]

vids = collection.find()

vids = [
    {
        "video_id": vid["video_id"],
        "title": vid["title"],
        "channel": vid["channel"],
        "date": vid["date"],
        "length_minutes": vid["stats"]["length_minutes"],
        "views": vid["stats"]["views"],
        "likes": vid["stats"]["likes"],
        "comments": vid["stats"]["comments"],
        "roberta_title_pos": vid["stats"]["sentiment_roberta"]["title_pos"],
        "roberta_title_neg": vid["stats"]["sentiment_roberta"]["title_neg"],
        "roberta_title_neu": vid["stats"]["sentiment_roberta"]["title_neu"],
    }
    for vid in vids
]


df = pd.DataFrame(vids)
# older videos have more views, so normalize by age. Full maturity when video is 2 months old
# also likes, comments

cutoff_date = df["date"].max()  # or pd.Timestamp.today() if you want current date

df["video_age_weeks"] = (cutoff_date - df["date"]).dt.days / 7


def weight_decay(age_weeks):
    if age_weeks <= 4:
        return 0.9**age_weeks
    else:
        return 0.6


df["weight"] = df["video_age_weeks"].apply(weight_decay)
df["views"] = df["views"] * df["weight"]
df["likes"] = df["likes"] * df["weight"]
df["comments"] = df["comments"] * df["weight"]


# normalize impact, max 1
df["sent_impact"] = df["roberta_title_pos"] - df["roberta_title_neg"]
df["sent_impact"] = df["views"] * df["sent_impact"]
df["sent_impact"] = df["sent_impact"] / df["sent_impact"].max()

# sort by date
df = df.sort_values(by=["date"])

# resample by week, summing impact, views, likes, comments
df = df.set_index("date")
df = df.resample("W").sum()

# calculate exponential moving averages for stats, decay = 0.2 per week

df["views"] = df["views"].ewm(alpha=0.2).mean()
df["likes"] = df["likes"].ewm(alpha=0.2).mean()
df["comments"] = df["comments"].ewm(alpha=0.2).mean()
df["sent_impact"] = df["sent_impact"].ewm(alpha=0.2).mean()

df = df.loc[:, ["sent_impact"]]

btc_usd = pd.read_csv("../../btc_usd_daily.csv")

# join btc price data
btc_usd["date"] = pd.to_datetime(btc_usd["date"])
btc_usd = btc_usd.set_index("date")
btc_usd["mean"] = btc_usd[["open", "close"]].mean(axis=1)
btc_usd = btc_usd.loc[:, ["mean"]]
btc_usd = btc_usd.rename(columns={"mean": "btc_usd"})
df = df.join(btc_usd)

import matplotlib.pyplot as plt

# show plot: btc price and impact (on the same graph) as a function of time, two y axes
# visualise sentiment as color of the line of btc price
fig, ax1 = plt.subplots()

color = "tab:red"
ax1.set_xlabel("date")
ax1.set_ylabel("btc_usd", color=color)
ax1.plot(df.index, df["btc_usd"], color=color)
ax1.tick_params(axis="y", labelcolor=color)

ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
ax2.set_ylabel(
    "sentiment impact", color="tab:blue"
)  # we already handled the x-label with ax1
ax2.bar(df.index, df["sent_impact"], color="tab:blue")
# make bars wider
for patch in ax2.patches:
    patch.set_width(7)

ax2.tick_params(axis="y", labelcolor="tab:blue")


plt.show(block=True)
