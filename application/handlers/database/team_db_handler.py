from __future__ import annotations

from application.handlers.database.base_db_handler import BaseDBHandler
from application.handlers.database.models import Team


class TeamDBHandler(BaseDBHandler):
    def __init__(self):
        super().__init__(Team)

    def create_new_team(self, team_data: dict):
        self.add_item(team_data)

    def get_team_by_id(self, team_id: dict):
        return self.find_item_by_id(team_id)

    def delete_team_by_id(self, team_id: str):
        return self.delete_item_by_id(team_id)

    def get_all_teams(self):
        return self.get_all_items()
