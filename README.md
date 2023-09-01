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
    WARNING:root:Rebuilding the api client, key: AIzaSyDUbZB.... Current key index: 0
    WARNING:root:Switching the api key, as the 0 key quota has been reached
    WARNING:root:Rebuilding the api client, key: AIzaSyBxPot.... Current key index: 1
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
7.  **Youtube topic tracker**:
    -  A tool that could be used for searching, scraping video transcripts from videos and generating a summary using GPT
    
Example usage :
    
```python
    
    yt_topic_tracker = YoutubeTopicTracker(
        topic="covid",
        top_vid_finder=model.factories.create_top_video_finder(),
        transcript_scraper=model.factories.create_transcript_scraper(),
        report_repository=None,
    )
    
    report = yt_topic_tracker.last_day_report(top_vid_number=3)
    print(report.report)
    
        """
    After analyzing the transcripts and data from three YouTube videos discussing the topic of COVID-19, several key themes and perspectives emerge. 

    The first video features Robert F. Kennedy Jr. discussing a potential 2024 presidential run, reparations, the COVID-19 vaccine, and science. The conversation seems to be a general discussion about his political views and aspirations, with COVID-19 being one of the many topics discussed. The video has garnered 75,757 views, indicating a significant interest in Kennedy's views on these topics.

    The second video, which is in Vietnamese, appears to be a profile of a woman who has played a significant role in the global response to the COVID-19 pandemic. The video has 60,723 views, suggesting that there is a considerable interest in stories of individuals making a difference during the pandemic.

    The third video features a critique of the left-wing response to COVID-19, with the speaker accusing them of fear-mongering about new variants and using the pandemic to justify lockdowns, censorship, and political payoffs. This video has 31,946 views, indicating that there is a substantial audience for this perspective as well.

    In conclusion, the discourse around COVID-19 on YouTube is diverse, with different perspectives represented and significant interest in each. The pandemic continues to be a topic of global concern and discussion, with debates about political responses, individual contributions, and the future implications of the virus.

    Sentiment: -0.1. The sentiment is slightly negative due to the ongoing concerns and debates about the COVID-19 pandemic.

        """

```
                                                
As an example of using the pipeline to collect data, extract sentiment and produce analysis of youtube's videos sentiment towards Bitcoin in time, with price overlay:

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
