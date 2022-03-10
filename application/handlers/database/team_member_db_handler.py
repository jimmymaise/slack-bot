from __future__ import annotations

import uuid

from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID

from application.handlers.database.base_db_handler import BaseDBHandler


class TeamMemberDBHandler(BaseDBHandler):
    def __init__(self, google_sheet_db, team_member_sheet):
        schema = (
            Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
            Column('user_id', String()),
            Column('team_id', String()),
            Column('is_manager', Boolean()),
        )
        super().__init__(google_sheet_db, team_member_sheet, schema)

    def add_user_to_team(self, user_id, team_id, is_manager):
        self.add_item({
            'user_id': user_id,
            'team_id': team_id,
            'is_manager': is_manager,
        })

    def remove_user_to_team(self, user_id, team_id):
        self.execute(
            self.table.delete()
            .where(self.table.c.user_id == user_id)
            .where(self.table.c.role_id == team_id),
        )

    def get_team_manager_id_by_team_id(self, team_id):
        result = self.execute(
            self.table.select()
            .filter(
                self.table.c.team_id == team_id,
                self.table.c.is_manager == 1,
            ),
        )
        print(result)

    def get_team_id_by_user_id(self, user_id):
        result = self.execute(
            self.table.select()
            .filter(
                self.table.c.user_id == user_id,
            ),
        )
        print(result)
