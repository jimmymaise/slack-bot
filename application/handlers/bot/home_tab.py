from __future__ import annotations

import json

from slack_bolt import App
from slack_bolt import BoltContext
from slack_sdk import WebClient

from application.handlers.bot.block_template_handler import BlockTemplateHandler
from application.handlers.bot.bot_utils import BotUtils
from application.handlers.bot.leave_lookup import LeaveLookup
from application.handlers.bot.leave_register import LeaveRegister
from application.handlers.bot.team_management import TeamManagement
from application.handlers.database.leave_registry_db_handler import LeaveRegistryDBHandler


class HomeTab:
    def __init__(
            self, app: App, client: WebClient, leave_lookup: LeaveLookup, leave_register: LeaveRegister,
            team_management: TeamManagement,
    ):
        self.app = app
        self.client = client
        self.leave_lookup = leave_lookup
        self.team_management = team_management
        app.event('app_home_opened')(ack=self.respond_to_slack_within_3_seconds, lazy=[self.open_app_home_lazy])
        app.action('book_vacation')(
            ack=self.respond_to_slack_within_3_seconds, lazy=[leave_register.trigger_request_leave_command],
        )
        app.action('check_ooo_today')(
            ack=self.respond_to_slack_within_3_seconds, lazy=[leave_lookup.trigger_today_ooo_command],
        )
        self.block_kit = BlockTemplateHandler('./application/handlers/bot/block_templates').get_object_templates()

        app.action('become_manager')(
            ack=self.respond_to_slack_within_3_seconds, lazy=[team_management.get_create_team_view_lazy],
        )
        app.action('my_all_time_offs')(
            ack=self.respond_to_slack_within_3_seconds, lazy=[self.get_my_time_off_lazy],
        )
        app.action('timeoff_type_filter')(
            ack=self.respond_to_slack_within_3_seconds, lazy=[self.get_my_time_off_lazy],
        )
        app.action('timeoff_start_filter')(
            ack=self.respond_to_slack_within_3_seconds, lazy=[self.get_my_time_off_lazy],
        )
        app.action('timeoff_end_filter')(
            ack=self.respond_to_slack_within_3_seconds, lazy=[self.get_my_time_off_lazy],
        )
        self.leave_register_db_handler = LeaveRegistryDBHandler()

    @staticmethod
    def respond_to_slack_within_3_seconds(ack):
        ack()

    def open_app_home_lazy(self, event, context: BoltContext, client: WebClient, body):
        if event['tab'] == 'home':
            self.team_management.get_personal_view_by_user_id(context.user_id)

    def get_my_time_off_lazy(self, body):
        user_id = body['user']['id']
        state = body['view']['state']
        leave_type = BotUtils.get_value_from_state(
            state, 'timeoff_type_filter', extra_field='selected_option.value',
            block_id='timeoff_filter',
        )
        start_date = BotUtils.get_value_from_state(
            state, 'timeoff_start_filter', extra_field='selected_date',
            block_id='timeoff_filter',
        )
        end_date = BotUtils.get_value_from_state(
            state, 'timeoff_end_filter', extra_field='selected_date',
            block_id='timeoff_filter',
        )
        blocks = self.leave_lookup.get_my_time_off_filter_blocks(
            user_id=user_id, start_date=start_date, end_date=end_date,
            leave_type=leave_type,
        )

        self.client.views_publish(
            user_id=user_id, view={
                'type': 'home',
                'blocks': blocks,
            },
        )

    def get_my_time_off_filter_blocks(self, user_id, start_date, end_date):
        user_leave_rows = self.leave_register_db_handler.get_leaves(
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
        )
        user_leaves = BotUtils.build_leave_display_list(user_leave_rows)
        blocks = json.loads(
            self.block_kit.all_your_time_off_blocks(
                user_leaves=user_leaves,
            ),
        )
        return blocks
