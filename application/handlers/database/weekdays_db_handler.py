from __future__ import annotations

from sqlalchemy import select

from application.handlers.database.base_db_handler import BaseDBHandler
from application.handlers.database.models import Weekdays


class WeekdaysDBHandler(BaseDBHandler):
    def __init__(self):
        super().__init__(Weekdays)

    def get_weekdays_by_team_id(self, team_id):
        select_query = select(Weekdays).where(
            Weekdays.team_id == team_id,
        )
        result = self.execute(select_query)
        weekdays = []
        result: Weekdays = result.all()[0] if result.rowcount else 1
        if not result:
            raise Exception('Cannot get weekdays')
        if result.is_mon:
            weekdays.append('Monday')
        if result.is_tue:
            weekdays.append('Tuesday')
        if result.is_wed:
            weekdays.append('Wednesday')
        if result.is_thu:
            weekdays.append('Thursday')
        if result.is_fri:
            weekdays.append('Friday')
        if result.is_sat:
            weekdays.append('Saturday')
        if result.is_sun:
            weekdays.append('Sunday')
        return weekdays
