from __future__ import annotations

import uuid

from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID

from application.handlers.database.base_db_handler import BaseDBHandler
from application.utils.constant import Constant
from application.utils.logger import Logger


class TeamMemberDBHandler(BaseDBHandler):
    def __init__(self):
        sheet = Constant.TEAM_MEMBER_SHEET
        schema = (
            Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
            Column('user_id', String(), primary_key=True),
            Column('team_id', String()),
            Column('is_manager', Boolean()),
        )
        super().__init__(sheet, schema)
        self.logger = Logger.get_logger()

    def add_user_to_team(self, user_id, team_id, is_manager):
        current_user_team_id = self.get_team_member_by_user_id(user_id).id
        is_added_in_this_team = current_user_team_id and current_user_team_id == team_id
        is_added_in_other_team = current_user_team_id and current_user_team_id != team_id
        if is_added_in_other_team:
            self.logger.error(f'Exist in other team {team_id}')
        if is_added_in_this_team:
            self.logger.info('Added in this team')
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

    def get_team_managers_by_team_id(self, team_id):
        result = self.execute(
            self.table.select()
                .filter(
                self.table.c.team_id == team_id,
                self.table.c.is_manager == 1,
                ),
        )
        return result.all() if result.rowcount else []

    def get_team_member_by_user_id(self, user_id):
        result = self.execute(
            self.table.select()
                .filter(
                self.table.c.user_id == user_id,
                ),
        )
        return result.first() if result.rowcount else None
