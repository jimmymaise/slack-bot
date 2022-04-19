from __future__ import annotations

from datetime import timedelta

from slack_bolt import App
from slack_sdk import WebClient

from application.handlers.bot.base_management import BaseManagement


class WorkingDayCalculation(BaseManagement):
    def __init__(
            self, app: App, client: WebClient, approval_channel,
    ):
        super().__init__(app, client)
        self.approval_channel = approval_channel

    def get_holidays_by_team_id(self):
        pass

    def get_weekdays_by_team_id(self):
        pass

    def get_working_days_from_date_range_by_team_id(self, team_id, start_date, end_date):
        delta = end_date - start_date  # returns timedelta
        holidays = self.get_holidays_by_team_id()
        weekdays = self.get_weekdays_by_team_id()
        working_days = []

        for i in range(delta.days + 1):
            day = start_date + timedelta(days=i)
            is_weekday = day.strftime('%A') not in weekdays
            is_holiday = day in holidays
            is_working_day = is_weekday and not is_holiday
            if is_working_day:
                working_days.append(day)
        return working_days
