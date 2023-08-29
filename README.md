# Youtube Video Scraping and Analysis Pipeline

This project is a tool designed to scrape and analyze YouTube content data. Below is an overview of its primary components and their functions:

## Core Components:

1.  **Top Video Finder**:
    
    -   Finds videos within a specific date range.
    -   The range can be subdivided based on a given time delta parameter and can return a set number of results for each partition.
    -   Accepts multiple YouTube Data API keys and rotates between them as quotas are reached.
    -   Offers two methods for scraping statistics: using the YT API client or the `yt-dlp` implementation. The `yt-dlp` method doesn't use the API key quota.
2.  **Transcript Scraper**:
    
    -   Extracts captions from videos.
    -   One method uses `yt-dlp` to retrieve available captions on YouTube.
    -   An alternative method uses the OpenAI Whisper model to transcribe segments of the video's audio. This method can handle multiple languages but may take longer.
    - "Combo" method uses both implementations. Firstly it tries to use the "cheap" yt-dlp method, but ignores automatically generated captions, as they are lower quality. When there are no manually added captions, then the Whisper extractor takes over.
3.  **Sentiment Rater**:
    
    -   Assesses the sentiment of the video title and its transcript.
    -   The first method uses the Roberta model from Hugging Face: [twitter-roberta-base-sentiment](https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment).
    -   A second method employs OpenAI GPT, which requires an API key.
4.  **Persistence**:
    -   Data is stored using a MongoDB repository.
5.  **Pipeline**:
    -   The Pipeline object, represented by the `IYtVidScrapingPipeline` interface, integrates various elements of the system to offer a streamlined unified interface. By supplying the configuration data and employing the pipeline's factory method, you can instantiate the desired pipeline object.


As an example, simple sentiment analysis youtube's videos sentiment towards Bitcoin in time, with price overlay:

![myplot](https://github.com/adam7171512/scrape/assets/117537530/59684e2b-4591-4944-9bdb-e4db747e0c49)

## Configuration File:

To operate the tool, a config.toml configuration file is required. Here's a basic structure for the configuration:

[api]  
yt_data_api_keys = [YOUR_YOUTUBE_API_KEYS]  
open_ai_api_key = YOUR_OPENAI_API_KEY  

[db]  
repository = "mongo"  
mongo_db_url = YOUR_MONGODB_URL  
db_name = YOUR_DB_NAME  
collection_name = YOUR_COLLECTION_NAME  

[scraper]  
transcript_scraper = CHOICE ("combo", "whisper", "yt-dlp")  
stats_scraper = CHOICE ("yt-dlp", "ytapi")  
pipeline = CHOICE ("std", "serial", "batch")  
overwrite_existing_data = BOOL (true or false)  
sentiment_rater = CHOICE ("roberta", "gpt", "finbert")  

[misc]  
btc_price_csv_path = "resources/btc_usd_daily.csv"  
