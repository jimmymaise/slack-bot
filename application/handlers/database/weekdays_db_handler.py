from __future__ import annotations

from sqlalchemy import select
from sqlalchemy import update

from application.handlers.database.base_db_handler import BaseDBHandler
from application.handlers.database.models import Weekdays


class WeekdaysDBHandler(BaseDBHandler):
    def __init__(self):
        super().__init__(Weekdays)

    def add_weekdays_config(self, team_id, weekdays):
        data = self._convert_weekdays_list_to_dict(weekdays)
        data.update({
            'team_id': team_id,
        })
        self.add_item(
            data,
        )

    def update_weekdays_config_by_team_id(self, team_id, weekdays):
        data = self._convert_weekdays_list_to_dict(weekdays)
        update_query = update(self.table).where(self.table.team_id == team_id).values(**data)
        self.execute(update_query)

    @staticmethod
    def _convert_weekdays_list_to_dict(weekdays):

        return {
            'is_mon': 'Monday' in weekdays,
            'is_tue': 'Tuesday' in weekdays,
            'is_wed': 'Wednesday' in weekdays,
            'is_thu': 'Thursday' in weekdays,
            'is_fri': 'Friday' in weekdays,
            'is_sat': 'Saturday' in weekdays,
            'is_sun': 'Sunday' in weekdays,
        }

    def get_weekdays_by_team_id(self, team_id):
        select_query = select(Weekdays).where(
            Weekdays.team_id == team_id,
        )
        result = self.execute(select_query)
        weekdays = []
        result: Weekdays = result.all()[0] if result.rowcount else None
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
