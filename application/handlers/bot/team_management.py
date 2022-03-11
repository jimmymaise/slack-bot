from __future__ import annotations

import json

from slack_bolt import App
from slack_bolt import BoltContext
from slack_sdk import WebClient

from application.handlers.bot.block_template_handler import BlockTemplateHandler
from application.handlers.bot.bot_utils import BotUtils
from application.handlers.bot.leave_lookup import LeaveLookup
from application.handlers.database.leave_registry_db_handler import LeaveRegistryDBHandler
from application.handlers.database.team_db_handler import TeamDBHandler
from application.handlers.database.team_member_db_handler import TeamMemberDBHandler


class TeamManagement:
    def __init__(
            self, app: App, client: WebClient, leave_lookup: LeaveLookup,
    ):
        self.app = app
        self.client = client
        self.block_kit = BlockTemplateHandler('./application/handlers/bot/block_templates').get_object_templates()
        self.leave_lookup = leave_lookup

        self.team_member_db_handler = TeamMemberDBHandler(
        )
        self.leave_register_db_handler = LeaveRegistryDBHandler()
        self.team_db_handler = TeamDBHandler()
        app.view('create_team_view')(
            ack=lambda ack: ack(response_action='clear'),
            lazy=[self.create_team_lazy],
        )
        app.action('switch_personal')(
            ack=self.respond_to_slack_within_3_seconds, lazy=[self.get_personal_view_by_user_id],
        )
        app.action('switch_manager')(
            ack=self.respond_to_slack_within_3_seconds, lazy=[self.get_manager_view_by_user_id],
        )

    @staticmethod
    def respond_to_slack_within_3_seconds(ack):
        ack()

    def get_create_team_view_lazy(self, event, context: BoltContext, client: WebClient, body):
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

    def create_team_lazy(self, client, body, ack):
        user_id = body['user']['id']
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

        self.team_member_db_handler.add_many_items(
            all_team_members,
        )
        self.get_manager_view_by_user_id(user_id)

    def get_personal_view_lazy(self, body):
        self.get_personal_view_by_user_id(body['user']['id'])

    def get_manager_view_by_user_id(self, user_id):
        self.client.views_publish(
            user_id=user_id,
            view={
                'type': 'home',
                'blocks': json.loads(
                    self.block_kit.manager_panel(
                    ),
                ), },
        )

    def get_personal_view_by_user_id(self, user_id):
        user = self.client.users_info(user=user_id).data['user']
        is_admin_or_owner = user['is_admin'] or user['is_owner']
        current_team = self.get_team_member_by_user_id(user_id)
        is_able_to_create_team = current_team is None and is_admin_or_owner
        is_already_manager = current_team and current_team.is_manager

        if current_team or is_admin_or_owner:
            blocks = json.loads(
                self.block_kit.personal_view(
                    is_able_to_create_team=is_able_to_create_team,
                    is_already_manager=is_already_manager,
                    user_leaves=[],
                ),
            )
        else:
            blocks = json.loads(self.block_kit.home_tab_not_member())

        self.client.views_publish(
            user_id=user_id, view={
                'type': 'home',
                'blocks': blocks,
            },
        )

    def get_manager_ids_from_team(self, team_id):
        managers = self.team_member_db_handler.get_team_managers_by_team_id(team_id)
        return [manager.id for manager in managers]

    def get_team_id_by_user_id(self, user_id):
        team = self.team_member_db_handler.get_team_member_by_user_id(user_id)
        return team.id if team else None

    def get_team_member_by_user_id(self, user_id):
        return self.team_member_db_handler.get_team_member_by_user_id(user_id)
