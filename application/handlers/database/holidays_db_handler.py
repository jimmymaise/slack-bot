from __future__ import annotations

from application.handlers.database.base_db_handler import BaseDBHandler
from application.handlers.database.models import Holidays


class HolidaysDBHandler(BaseDBHandler):
    def __init__(self):
        super().__init__(Holidays)
