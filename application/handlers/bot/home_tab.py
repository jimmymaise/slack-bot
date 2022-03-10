from __future__ import annotations

import json

from slack_bolt import App
from slack_bolt import BoltContext
from slack_sdk import WebClient

from application.handlers.bot.block_template_handler import BlockTemplateHandler
from application.handlers.bot.leave_lookup import LeaveLookup
from application.handlers.bot.leave_register import LeaveRegister
from application.handlers.bot.team_management import TeamManagement


class HomeTab:
    def __init__(
        self, app: App, client: WebClient, leave_lookup: LeaveLookup, leave_register: LeaveRegister,
        team_management: TeamManagement,
    ):
        self.app = app
        self.client = client
        app.event('app_home_opened')(ack=self.respond_to_slack_within_3_seconds, lazy=[self.open_app_home_lazy])
        app.block_action({'block_id': 'home_tab', 'action_id': 'book_vacation'})(
            ack=self.respond_to_slack_within_3_seconds, lazy=[leave_register.trigger_request_leave_command],
        )
        self.block_kit = BlockTemplateHandler('./application/handlers/bot/block_templates').get_object_templates()

        app.block_action({'block_id': 'home_tab', 'action_id': 'become_manager'})(
            ack=self.respond_to_slack_within_3_seconds, lazy=[team_management.get_create_team_view_lazy],
        )

    @staticmethod
    def respond_to_slack_within_3_seconds(ack):
        ack()

    def open_app_home_lazy(self, event, context: BoltContext, client: WebClient):
        if event['tab'] == 'home':
            client.views_publish(
                user_id=context.user_id, view={
                    'type': 'home',
                    'blocks': json.loads(self.block_kit.home_tab()),
                },
            )
