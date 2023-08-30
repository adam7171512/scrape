# Youtube Video Scraping and Analysis Pipeline

This project is a tool designed to scrape and analyze YouTube content data. Below is an overview of its primary components and their functions:

## Core Components:

1.  **Top Video Finder**:
    
    -   Finds videos within a specific date range.
    -   The range can be subdivided based on a given time delta parameter and can return a set number of results for each partition.
    -   Accepts multiple YouTube Data API keys and rotates between them as quotas are reached.
    -   Offers two methods for scraping statistics: using the YT API client or the `yt-dlp` implementation. The `yt-dlp` method doesn't use the API key quota.
  
      Example usage :
    
    ```python
    # Should yield 3 batches of videos, 3 videos per batch
    top_vid_finder: IYtTopVideoFinder = model.factories.create_top_video_finder()
    top_videos = top_vid_finder.scrape_top_videos_with_stats(
        topic="Tesla",
        date_start=datetime.date(2023, 1, 1),
        date_end=datetime.date(2023, 3, 31),
        time_delta=30,
        max_results_per_time_delta=3,
    )

    n = 0
    total = 0
    for video_batch in top_videos:
        n += 1
        print(f'{10 * "="} Time search partition number {n}{10 * "="}')
        for vid in video_batch:
            total += 1
            print(f'Video number {total} : {vid.title}')
            print(f'Published at : {vid.date.isoformat()} , views: {vid.stats.views}')

    """
    WARNING:root:Rebuilding the api client, key: AIzaSyDUbZBzqCXmS_cYeicngle-jwlCUd41Mnc. Current key index: 0
    WARNING:root:Switching the api key, as the 0 key quota has been reached
    WARNING:root:Rebuilding the api client, key: AIzaSyBxPotinbqazTR7WV3A7w6p3Qui9JTmzZY. Current key index: 1
    ========== Time search partition number 1==========
    Video number 1 : 100 YouTubers Signed My Tesla!
    Published at : 2023-01-14T15:45:03+00:00 , views: 10079881
    Video number 2 : Smart, seductive, dangerous AI robots. Beyond GPT-4.
    Published at : 2023-01-22T16:57:44+00:00 , views: 4838283
    Video number 3 : 13 sorprendentes PREDICCIONES de Nikola TESLA sobre el futuro
    Published at : 2023-01-28T20:30:02+00:00 , views: 2650308
    ========== Time search partition number 2==========
    Video number 4 : Nikola Tesla Reveals Terrifying Truth About The Pyramids
    Published at : 2023-02-04T14:46:18+00:00 , views: 7322582
    Video number 5 : Watch Before They DELETE This.
    Published at : 2023-02-07T17:52:25+00:00 , views: 5374327
    Video number 6 : CÓMO CONSEGUIR ELECTRICIDAD GRATIS PARA SIEMPRE - EL INVENTO OCULTO DE TESLA
    Published at : 2023-02-20T17:41:22+00:00 , views: 4878489
    ========== Time search partition number 3==========
    Video number 7 : Driving A Tesla Upside-Down (10ft Tall Wheels)
    Published at : 2023-03-15T21:29:09+00:00 , views: 11019347
    Video number 8 : Tesla Model X PLAID v Ferrari SF90 v Lambo SVJ: DRAG RACE
    Published at : 2023-03-12T09:09:24+00:00 , views: 5857678
    Video number 9 : How Lexus Fixed Tesla&#39;s Bad Idea: Steer-By-Wire Yoke
    Published at : 2023-03-17T14:00:01+00:00 , views: 3944801
    """
    ```

    
3.  **Transcript Scraper**:
    
    -   Extracts captions from videos.
    -   One method uses `yt-dlp` to retrieve available captions on YouTube.
    -   An alternative method uses the OpenAI Whisper model to transcribe segments of the video's audio. This method can handle multiple languages but may take longer.
    - "Combo" method uses both implementations. Firstly it tries to use the "cheap" yt-dlp method, but ignores automatically generated captions, as they are lower quality. When there are no manually added captions, then the Whisper extractor takes over.
  
      Example usage :
    
    ```python
    # Yt-dlp scraper
    yt_dlp_transcript_scraper: IYtTranscriptScraper = YtDlpTranscriptScraper(
        include_auto_captions=True
    )
    transcript = transcript_scraper.scrape_transcript("wiUiL9vw24A")
    print(transcript[:300])
    """
     idiot just vandalized my wife's car plan is simple pretend this match my window so it can go to the
    """

    # Whisper scraper
    whisper_scraper: IYtTranscriptScraper = YtWhisperTranscriptScraper(
        whisper=WhisperTranscriptExtractor(),
        yt_audio_downloader=YtAudioDownloader(length_min=5),
    )

    transcript = whisper_scraper.scrape_transcript("wiUiL9vw24A")
    print(transcript[:300])

    """
     Some idiot just vandalized my wife's car. The plan is simple. Pretend to smash my wife's window so it can go to the shop. Actually, get that Tesla wrap in her favorite color, Tiffany Blue. Tell her          we're just taking a boys trip, but instead we're actually driving 100 hours to get her car signed by
    """
    ```

4.  **Sentiment Rater**:
    
    -   Assesses the sentiment of the video title and its transcript.
    -   The first method uses the Roberta model from Hugging Face: [twitter-roberta-base-sentiment](https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment).
    -   A second method employs OpenAI GPT, which requires an API key.

      Example usage :
    
    ```python
    # Roberta:
    roberta_sent_rater: ISentimentRater = RobertaSentimentRater()
    score = roberta_sent_rater.rate(
        "Some idiot just vandalized my wife's car. The plan is simple. Pretend to smash my wife's window so it can go to the shop."
    ).score
    print(f'Sentiment rating score: {score}')
    """
     Sentiment rating score: -0.93
    """

    # Gpt
    wgpt_sent_rater: ISentimentRater = GptSentimentRater(
        config_data_provider.get_open_ai_api_key(),
    )
    score = gpt_sent_rater.rate(
        "Some idiot just vandalized my wife's car. The plan is simple. Pretend to smash my wife's window so it can go to the shop."
    ).score
    print(f'Sentiment rating score: {score}')

    """
     Sentiment rating score: -0.5
    """
    ```
      
5.  **Persistence**:
    -   Data is stored using a MongoDB repository.
6.  **Pipeline**:
    -   The Pipeline object, represented by the `IYtVidScrapingPipeline` interface, integrates various elements of the system to offer a streamlined unified interface. By supplying the configuration data and employing the pipeline's factory method, you can instantiate the desired pipeline object.

      Pipeline objects are initialized using repository, video finder, transcript scraper and sentiment rater.
    
                                                    
As an example, simple sentiment analysis youtube's videos sentiment towards Bitcoin in time, with price overlay:

![myplot](https://github.com/adam7171512/scrape/assets/117537530/76b928c2-3ca2-458b-af03-e99583ff90fa)


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
