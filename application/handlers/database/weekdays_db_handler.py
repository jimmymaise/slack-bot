from __future__ import annotations

from application.handlers.database.base_db_handler import BaseDBHandler
from application.handlers.database.models import Weekdays


class WeekdaysDBHandler(BaseDBHandler):
    def __init__(self):
        super().__init__(Weekdays)
