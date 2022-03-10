from __future__ import annotations

import uuid

from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID

from application.handlers.database.base_db_handler import BaseDBHandler


class TeamDBHandler(BaseDBHandler):
    def __init__(self, google_sheet_db, team_sheet):
        schema = (
            Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
            Column('name', String()),
            Column('announcement_channel_id', String()),
            Column('holiday_country', String()),
        )
        super().__init__(google_sheet_db, team_sheet, schema)

    def create_new_team(self, team_data: dict):
        self.add_item(team_data)
