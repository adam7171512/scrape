import numpy as np
import pandas as pd
from pymongo import MongoClient
from pymongo.collection import Collection
from scipy.special import softmax
from transformers import AutoConfig

from model.yt_tools.yt_top_vid_finder import RobertaSentiment, YtVideo

MODEL = f"cardiffnlp/twitter-roberta-base-sentiment"
config = AutoConfig.from_pretrained(MODEL)
from transformers import AutoModelForSequenceClassification, AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")

client = MongoClient("mongodb://localhost:27017")


def get_roberta_sentiment(text: str) -> dict:
    encoded_input = tokenizer(text, return_tensors="pt", max_length=510)
    output = model(**encoded_input)
    scores = output[0][0].detach().numpy()
    scores = softmax(scores)
    ranking = np.argsort(scores)
    rank_scores = dict(zip(ranking, scores[ranking]))
    return {
        "positive": float(rank_scores[0]),
        "neutral": float(rank_scores[2]),
        "negative": float(rank_scores[1]),
    }


def assign_roberta_sentiment(col: Collection):
    videos_without_transcript = []
    for doc in col.find():
        vid_title = doc.get("title", None)
        transcript = doc.get("transcript", None)

        v = YtVideo(**doc)
        if vid_title and v.stats.sentiment_roberta.title_pos:
            print(f"setting title sentiment for {v.title}")

            rs = v.stats.sentiment_roberta

            if True:
                roberta_title_sentiment = get_roberta_sentiment(vid_title)
                rs = RobertaSentiment(
                    title_pos=roberta_title_sentiment["positive"],
                    title_neu=roberta_title_sentiment["neutral"],
                    title_neg=roberta_title_sentiment["negative"],
                )
            if transcript:
                print(f"setting transcript sentiment for {v.title}")
                roberta_transcript_sentiment = get_roberta_sentiment(transcript)
                rs.transcript_pos = roberta_transcript_sentiment["positive"]
                rs.transcript_neu = roberta_transcript_sentiment["neutral"]
                rs.transcript_neg = roberta_transcript_sentiment["negative"]
            else:
                videos_without_transcript.append(v)
            v.stats.sentiment_roberta = rs
            print(f"updated {v.title}")
            print(rs.model_dump())
            col.update_one({"_id": doc["_id"]}, {"$set": v.model_dump()})

    # vids without transcript to csv :
    df = pd.DataFrame([v.dict() for v in videos_without_transcript])
    df.to_csv("videos_without_transcript.csv")


db = client["yt_new"]

collection = db["crypto_videos_weekly_2"]

assign_roberta_sentiment(collection)
