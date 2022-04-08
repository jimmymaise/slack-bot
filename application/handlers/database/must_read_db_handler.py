from __future__ import annotations

from sqlalchemy import select

from application.handlers.database.base_db_handler import BaseDBHandler
from application.handlers.database.models import MustReadMessage


class MustReadDBHandler(BaseDBHandler):
    def __init__(self):
        super().__init__(MustReadMessage)

    def get_must_read_messages(self, statuses=None, author_user_id=None):
        select_query = select(self.table)
        if statuses is not None:
            select_query = select_query.filter(
                self.table.status.in_(statuses),
            )
        if author_user_id is not None:
            select_query = select_query.filter(self.table.author_user_id == author_user_id)
        select_query = select_query.order_by(self.table.message_ts.desc())
        result = self.execute(select_query)
        return result.all() if result.rowcount else []

    def add_must_read_messages(self, message_ts, author_user_id, status, short_content, permalink, channel):
        self.add_item(
            data={
                ''
                'message_ts': message_ts,
                'author_user_id': author_user_id,
                'status': status,
                'short_content': short_content,
                'permalink': permalink,
                'channel': channel,
            },
        )

    def get_team_by_id(self, team_id: dict):
        return self.find_item_by_id(team_id)

    def delete_team_by_id(self, team_id: str):
        return self.delete_item_by_id(team_id)

    def get_all_teams(self):
        return self.get_all_items()
