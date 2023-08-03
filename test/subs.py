from model.yt_tools.yt_transcript_scraper import YtYtDlpTranscriptScraper

sub_scraper = YtYtDlpTranscriptScraper()
print(sub_scraper.scrape_from_url("https://www.youtube.com/watch?v=kLQQo9wvmfo", include_auto_captions=False))