from pymongo import MongoClient

from gpt_tools.tools import GptContact

client = MongoClient("mongodb://localhost:27017")
db = client["youtube"]
collection = db["videos_weekly_cryptocurrency"]

videos = collection.find()


def get_title_sentiment(text):
    try:
        rating = GptContact.get_chat_completion(
            system_message=f"Rate the headline sentiment. Use values between -100 and 100 \n"
            f"### Guidelines for rating: (but you can use value in between too) :\n"
            f"-100 : very negative\n"
            f"-50: negative\n"
            f"0: neutral\n"
            f"50: positive\n"
            f"100: very positive\n"
            f"### Required answer format:\n"
            f"sentiment_rating = <rating>",
            user_message=text,
            max_tokens=15,
            temperature=0,
            model="gpt-3.5-turbo",
        )
        str_rating = ""
        # look for number in the response
        for char in rating:
            if char.isdigit() or char == "-":
                str_rating += char

        rating = int(str_rating)

        print(f'rating for "{text}" is {rating}')
        return rating
    except:
        return 0


for video in videos:
    if video.get("title_sentiment") == None:
        print(f"getting title sentiment for {video['video_id']}")
        title_sentiment = get_title_sentiment(video["title"])
        video["title_sentiment"] = title_sentiment
        print(video["title_sentiment"])
        collection.update_one({"_id": video["_id"]}, {"$set": video})
    else:
        print(f"skipping {video['video_id']}")
