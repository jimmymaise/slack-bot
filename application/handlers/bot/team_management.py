from __future__ import annotations

import datetime
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
        app.view('update_team_view')(
            ack=lambda ack: ack(response_action='clear'),
            lazy=[self.create_team_lazy],
        )
        app.action('switch_personal')(
            ack=self.respond_to_slack_within_3_seconds, lazy=[self.get_personal_view_by_user_id],
        )
        app.action('back_to_home')(
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
                self.block_kit.create_update_team_view(
                    callback_id='create_team_view',
                    initial_team_name=f"{user_name}'s team",
                    initial_managers=[context.user_id],
                    title='Create a team',
                    submit_type='Create',
                ),
            ),
        )

    def get_update_team_view_lazy(self, event, context: BoltContext, client: WebClient, body):
        team_id = self.get_team_id_by_user_id(context.user_id)
        team_info = self.get_team_by_team_id(team_id)
        all_team_members = self.team_member_db_handler.get_all_team_members_by_team_id(team_id=team_id)
        client.views_open(
            trigger_id=body.get('trigger_id'),
            view=json.loads(
                self.block_kit.create_update_team_view(
                    callback_id='update_team_view',
                    initial_team_name=team_info.name,
                    initial_managers=[
                        member.user_id for member in all_team_members if
                        member.is_manager is True
                    ],
                    initial_normal_members=[
                        member.user_id for member in all_team_members if
                        member.is_manager is False
                    ],
                    initial_conversation=team_info.announcement_channel_id,
                    title='Update team',
                    submit_type='Update',
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
        team_id = self.get_team_id_by_user_id(user_id)
        team_info = self.get_team_by_team_id(team_id)
        announcement_channel_name = \
            self.client.conversations_info(channel=team_info.announcement_channel_id)['channel']['name']
        all_team_members = self.team_member_db_handler.get_all_team_members_by_team_id(team_id=team_id)
        num_of_all_team_member = len(all_team_members)
        num_of_manager = sum(1 for team_member in all_team_members if team_member.is_manager)
        num_of_normal_member = num_of_all_team_member - num_of_manager
        slack_users = BotUtils.get_slack_users_by_user_ids(
            self.client,
            [team_member.user_id for team_member in all_team_members],
        )
        self.client.views_publish(
            user_id=user_id,
            view={

                'type': 'home',
                'blocks': json.loads(
                    self.block_kit.manager_panel(
                        team_info=team_info,
                        announcement_channel_name=announcement_channel_name,
                        num_of_normal_member=num_of_normal_member,
                        num_of_manager=num_of_manager,
                        all_team_members=all_team_members,
                        slack_users=slack_users,
                    ),
                ), },
        )

    def get_personal_view_by_user_id(self, user_id):
        user = self.client.users_info(user=user_id).data['user']
        is_admin_or_owner = user['is_admin'] or user['is_owner']
        current_team = self.get_team_member_by_user_id(user_id)
        team_name = self.get_team_by_team_id(team_id=current_team.team_id).name if current_team else None
        is_able_to_create_team = current_team is None and is_admin_or_owner
        is_already_manager = current_team and current_team.is_manager
        is_not_have_team = not (current_team or is_admin_or_owner)

        user_leave_rows = self.leave_register_db_handler.get_leaves(
            start_date=datetime.datetime.now().strftime('%Y-%m-%d'),
            user_id=user_id,
        )

        user_leaves = BotUtils.build_leave_display_list(user_leave_rows)

        blocks = json.loads(
            self.block_kit.personal_view(
                is_able_to_create_team=is_able_to_create_team,
                is_already_manager=is_already_manager,
                is_not_have_team=is_not_have_team,
                user_leaves=user_leaves,
                team_name=team_name,
            ),
        )

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
        return team.team_id if team else None

    def get_team_member_by_user_id(self, user_id):
        return self.team_member_db_handler.get_team_member_by_user_id(user_id)

    def get_team_by_team_id(self, team_id):
        return self.team_db_handler.get_team_by_id(team_id)
