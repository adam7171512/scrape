from typing import Protocol

from pydantic import BaseModel

from model.gpt_tools.tools import GptContact
from model.youtube.core import IYtTopVideoFinder, IYtTranscriptScraper, YtVideo
import datetime
import config_data_provider


class TopicReport(BaseModel):
    date_start: datetime.date
    date_end: datetime.date
    topic: str
    videos: list[YtVideo]
    report: str


class IReportRepository(Protocol):

    def save_report(self, report: TopicReport) -> None:
        ...


class GptTopicReporter:

    def __init__(
            self,
            topic: str,
    ):
        self.topic = topic
        self.gpt_contact = GptContact(config_data_provider.get_open_ai_api_key(), model="gpt-4")
        self.gpt_contact.set_system_message(
            f"You will be presented with a list of youtube videos and their data, including the transcript. "
            f"Your job is to draw conclusions from the findings and write a short report about the topic, just"
            f"like you would do if you were a journalist. At the end, Rate the sentiment of the report, "
            f"ranging from -1 for very negative to 1 for very positive"
            f"\nTopic: {topic}\n"
        )

    def report(self, date_start: datetime.date, date_end: datetime.date, videos: list[YtVideo]) -> TopicReport:
        videos_str = "\n".join([
            f"\n\n\n{i}. {v.title} views: ({v.stats.views} \n transcript: \n{v.transcript})" for i, v in enumerate(videos)
        ])

        print(f'number of videos: {len(videos)}')

        self.gpt_contact.add_user_message(f"Here are the videos: {videos_str}")

        report = self.gpt_contact.get_completion(
            temperature=0,
            max_response_tokens=1000,
        )

        return TopicReport(
            date_start=date_start,
            date_end=date_end,
            topic=self.topic,
            videos=videos,
            report=report,
        )


class YoutubeTopicTracker:

    def __init__(
            self,
            topic: str,
            top_vid_finder: IYtTopVideoFinder,
            transcript_scraper: IYtTranscriptScraper,
            report_repository: IReportRepository | None = None,
    ):
        self.topic = topic
        self.top_vid_finder = top_vid_finder
        self.transcript_scraper = transcript_scraper
        self.report_repository = report_repository
        self.topic_reporter = GptTopicReporter(topic)

    def last_day_report(self, top_vid_number: int = 1) -> TopicReport:
        last_day = datetime.date.today() - datetime.timedelta(days=1)
        videos: list[YtVideo] = list(self.top_vid_finder.scrape_top_videos_with_stats(
            topic=self.topic,
            date_start=last_day,
            date_end=last_day,
            time_delta=1,
            max_results_per_time_delta=top_vid_number,
            min_video_length=5,
        ))[0]

        for video in videos:
            video.transcript = self.transcript_scraper.scrape_transcript(video.video_id)[:500]

        report = self.topic_reporter.report(
            date_start=last_day,
            date_end=last_day,
            videos=videos,
        )

        if self.report_repository:
            self.report_repository.save_report(report)

        return report
