from __future__ import annotations

from application.handlers.database.base_db_handler import BaseDBHandler
from application.handlers.database.models import HolidayGroups


class HolidayGroupsDBHandler(BaseDBHandler):
    def __init__(self):
        super().__init__(HolidayGroups)
