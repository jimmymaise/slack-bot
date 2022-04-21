from __future__ import annotations

from sqlalchemy import select

from application.handlers.database.base_db_handler import BaseDBHandler
from application.handlers.database.models import HolidayGroups
from application.handlers.database.models import Holidays
from application.handlers.database.models import Team


class HolidaysDBHandler(BaseDBHandler):
    def __init__(self):
        super().__init__(Holidays)

    def get_holidays_by_team_id(self, team_id, start_date=None, end_date=None):
        select_query = select(Holidays).join(
            HolidayGroups, Holidays.holiday_group_id == HolidayGroups.id,
        ).join(
            Team, HolidayGroups.id == Team.holiday_group_id,
        )
        if start_date:
            select_query = select_query.where(
                Holidays.date >= start_date,
            )
        if end_date:
            select_query = select_query.where(
                Holidays.date <= end_date,
            )
        result = self.execute(select_query)
        return result.all() if result.rowcount else []
