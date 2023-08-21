import glob
import re

from pymongo import MongoClient
from pymongo.collection import Collection
from transformers import AutoConfig, AutoModelForSequenceClassification, AutoTokenizer

from model.yt_tools.yt_top_vid_finder import YtVideo

MODEL = f"cardiffnlp/twitter-roberta-base-sentiment-latest"
tokenizer = AutoTokenizer.from_pretrained(MODEL)
config = AutoConfig.from_pretrained(MODEL)
model = AutoModelForSequenceClassification.from_pretrained(MODEL)

client = MongoClient("mongodb://localhost:27017")
db = client["yt_new"]
collection = db["bitcoin"]


# video id is placed inside the file name in brackes [] , for example rewrew[dasdasad].txt  , id is dasdasad
def get_vid_id(filepath: str) -> str:
    return re.search(r"\[(.*?)\]", filepath).group(1)


def get_ids_from_folder(folder: str) -> dict:
    ids = {}
    for file in glob.glob(f"{folder}/*.txt"):
        ids[get_vid_id(file)] = file
    return ids


def fill_missing_transcripts(collection: Collection, transcripts_folder: str):
    ids = get_ids_from_folder(transcripts_folder)

    for id_ in ids.keys():
        doc = collection.find_one({"video_id": id_})
        if doc:
            d_id = doc["_id"]
            doc = YtVideo(**doc)
            if doc.transcript is None:
                with open(f"{ids[id_]}", "r") as f:
                    doc.transcript = f.read()
                collection.update_one({"_id": d_id}, {"$set": doc.model_dump()})
                print(f"updated {doc.title}")
        else:
            print(f"no doc found for {id_}")


def get_vids_without_transcript(collection: Collection):
    ids = collection.find({"transcript": None})
    import pandas as pd

    df = pd.DataFrame(ids)
    df.to_csv("videos_without_transcript.csv")


def transcript_transplants_between_collections(
    donor_collection, recipient_collection
) -> list[str]:
    for vid in recipient_collection.find({"transcript": None}):
        obj_id = vid["_id"]
        vid = YtVideo(**vid)
        matching_vid = donor_collection.find_one({"video_id": vid.video_id})
        if matching_vid and matching_vid.get("transcript", None):
            vid.transcript = matching_vid["transcript"]
            recipient_collection.update_one({"_id": obj_id}, {"$set": vid.model_dump()})
            print(f"updated {vid.title}")


# old_col = client["yt_new"]["crypto_videos_weekly"]
# new_col = client["yt_new"]["bitcoin"]
# transcript_transplants_between_collections(donor_collection=old_col, recipient_collection=new_col)

# fill_missing_transcripts(collection=collection, transcripts_folder="transcripts")

get_vids_without_transcript(collection=collection)
