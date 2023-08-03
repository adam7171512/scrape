from pymongo.collection import Collection

from model.transcript_filler import create_whisper_transcript_filler
from model.trash_utils.sentiment_analysis.sentiment_roberta import RobertaSentimentRater
from model.yt_tools.yt_mongo_repository import (
    YtMongoRepository,
    YtMongoRepositoryFactory,
)

# filler = create_transcript_filler(db_name="youtube", collection_name="cryptocurrency_daily")
# filler.fill_missing_transcripts()

yt_mongo_repository = YtMongoRepositoryFactory(
    "youtube", "cryptocurrency_daily"
).create()
roberta = RobertaSentimentRater(yt_mongo_repository)
roberta.assign_roberta_sentiment_for_all()
