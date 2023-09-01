import datetime
from typing import Protocol


class IYtVidScrapingPipeline(Protocol):
    def process(
        self,
        topic: str,
        date_start: datetime.date,
        date_end: datetime.date,
        time_delta: int,
        max_results_per_time_delta: int = 10,
        language: str = None,
        stats_lower_limit: int | None = None,
        length_minutes_lower_limit: int | None = None,
    ) -> None:
        ...
