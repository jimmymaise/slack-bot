from __future__ import annotations

import json

from slack_bolt import App
from slack_bolt import BoltContext
from slack_sdk import WebClient

from application.handlers.bot.block_template_handler import BlockTemplateHandler
from application.handlers.bot.bot_utils import BotUtils
from application.handlers.database.google_sheet import GoogleSheetDB
from application.handlers.database.team_db_handler import TeamDBHandler
from application.handlers.database.team_member_db_handler import TeamMemberDBHandler


class TeamManagement:
    def __init__(
            self, app: App, client: WebClient, google_sheet_db: GoogleSheetDB,
            team_sheet, team_member_sheet,
    ):
        self.app = app
        self.client = client
        self.block_kit = BlockTemplateHandler('./application/handlers/bot/block_templates').get_object_templates()
        self.google_sheet_db = google_sheet_db
        self.team_sheet = team_sheet
        self.team_member_sheet = team_member_sheet

        self.team_member_db_handler = TeamMemberDBHandler(
            google_sheet_db=google_sheet_db,
            team_member_sheet=team_member_sheet,
        )
        self.team_db_handler = TeamDBHandler(
            google_sheet_db=google_sheet_db,
            team_sheet=team_sheet,
        )
        app.view('create_team_view')(
            ack=lambda ack: ack(response_action='clear'),
            lazy=[self.create_team],
        )

    @staticmethod
    def respond_to_slack_within_3_seconds(ack):
        ack()

    def create_team_lazy(self, event, context: BoltContext, client: WebClient, body):
        user_name = BotUtils.get_username_by_user_id(client, context.user_id)
        client.views_open(
            trigger_id=body.get('trigger_id'),
            view=json.loads(
                self.block_kit.create_team_view(
                    callback_id='create_team_view',
                    user_name=user_name,
                    user_id=context.user_id,
                ),
            ),
        )

    def create_team(self, client, body, ack):
        state = body['view']['state']
        team_name = BotUtils.get_value_from_state(state, 'name', 'value')
        managers = BotUtils.get_value_from_state(state, 'managers', 'selected_users')
        normal_members = BotUtils.get_value_from_state(state, 'members', 'selected_users')
        announcement_channel_id = BotUtils.get_value_from_state(state, 'channel', 'selected_conversation')
        team_id = self.team_db_handler.add_item(
            data={
                'announcement_channel_id': announcement_channel_id,
                'name': team_name,
                'holiday_country': 'US',

            },
        )

        all_team_members = [{'user_id': manager, 'is_manager': True, 'team_id': team_id} for manager in managers]
        all_team_members += [
            {'user_id': normal_member, 'is_manager': False, 'team_id': team_id} for normal_member in
            normal_members
        ]

        # self.team_member_db_handler.add_many_items(
        #     all_team_members
        # )

        announcement_channel_id = body['view']['state']['values']['channel']['channel_value']['selected_conversation']
        announcement_channel_id = body['view']['state']['values']['channel']['channel_value']['selected_conversation']

        pass
