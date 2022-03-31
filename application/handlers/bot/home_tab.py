from __future__ import annotations

import re

from slack_bolt import App
from slack_bolt import BoltContext
from slack_sdk import WebClient

from application.handlers.bot.base_management import BaseManagement
from application.handlers.bot.leave_lookup import LeaveLookup
from application.handlers.bot.leave_register import LeaveRegister
from application.handlers.bot.team_management import TeamManagement


class HomeTab(BaseManagement):
    def __init__(
            self, app: App, client: WebClient, leave_lookup: LeaveLookup, leave_register: LeaveRegister,
            team_management: TeamManagement,
    ):
        super().__init__(app, client)
        self.leave_lookup = leave_lookup
        self.leave_register = leave_register
        self.team_management = team_management
        app.event('app_home_opened')(ack=self.respond_to_slack_within_3_seconds, lazy=[self.open_app_home_lazy])
        app.action('book_vacation')(
            ack=self.respond_to_slack_within_3_seconds, lazy=[leave_register.trigger_request_leave_command],
        )
        app.action('check_ooo_today')(
            ack=self.respond_to_slack_within_3_seconds, lazy=[leave_lookup.trigger_today_ooo_command],
        )

        app.action('become_manager')(
            ack=self.respond_to_slack_within_3_seconds, lazy=[team_management.get_create_team_view_lazy],
        )
        app.action('team_settings_home')(
            ack=self.respond_to_slack_within_3_seconds, lazy=[team_management.get_update_team_view_lazy],
        )
        app.action('my_all_time_offs')(
            ack=self.respond_to_slack_within_3_seconds, lazy=[self.get_my_time_off_lazy],
        )
        app.action('team_timeoffs')(
            ack=self.respond_to_slack_within_3_seconds, lazy=[self.get_my_team_time_off_lazy],
        )
        app.action(re.compile('your_timeoff_.*'))(
            ack=self.respond_to_slack_within_3_seconds, lazy=[self.get_my_time_off_lazy],
        )
        app.action(re.compile('team_timeoff.*'))(
            ack=self.respond_to_slack_within_3_seconds, lazy=[self.get_my_team_time_off_lazy],
        )
        app.action('accept_request_home')(
            ack=self.respond_to_slack_within_3_seconds, lazy=[self.process_block_leave_action_from_manager_home],
        )
        app.action('reject_request_home')(
            ack=self.respond_to_slack_within_3_seconds, lazy=[self.process_block_leave_action_from_manager_home],
        )

        app.action('overflow_timeoff_actions_home_personal')(
            ack=self.respond_to_slack_within_3_seconds, lazy=[self.process_overflow_leave_action_from_personal_home],
        )

    @staticmethod
    def respond_to_slack_within_3_seconds(ack):
        ack()

    def process_block_leave_action_from_manager_home(self, body, ack):
        self.leave_register.take_action_on_leave_from_action_block(body, ack)
        self.team_management.get_manager_view_by_user_id(body['user']['id'])

    def process_overflow_leave_action_from_personal_home(self, body, ack):
        self.leave_register.take_action_on_leave_from_overflow_block(body, ack)
        self.team_management.get_personal_view_by_user_id(body['user']['id'])

    @staticmethod
    def get_panel(event):
        try:
            return event['view']['blocks'][0]['text']['text']
        except KeyError:
            return None

    def open_app_home_lazy(self, event, context: BoltContext, client: WebClient, body):
        if event['tab'] == 'home':
            if self.get_panel(event) == '*Manager panel*':
                self.team_management.get_manager_view_by_user_id(context.user_id)
            else:
                self.team_management.get_personal_view_by_user_id(context.user_id)

    def get_my_time_off_lazy(self, body):
        user_id = body['user']['id']
        state = body['view']['state']
        leave_type = self.leave_lookup.get_value_from_state(
            state, 'your_timeoff_type_filter', extra_field='selected_option.value',
            block_id='timeoff_filter',
        )
        start_date = self.leave_lookup.get_value_from_state(
            state, 'your_timeoff_start_filter', extra_field='selected_date',
            block_id='timeoff_filter',
        )
        end_date = self.leave_lookup.get_value_from_state(
            state, 'your_timeoff_end_filter', extra_field='selected_date',
            block_id='timeoff_filter',
        )
        statuses = [
            self.constant.LEAVE_REQUEST_STATUS_WAIT,
            self.constant.LEAVE_REQUEST_STATUS_APPROVED,
            self.constant.LEAVE_REQUEST_STATUS_REJECTED,
        ]

        blocks = self.leave_lookup.get_my_time_off_filter_blocks(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            leave_type=leave_type,
            statuses=statuses,
        )

        self.client.views_publish(
            user_id=user_id, view={
                'type': 'home',
                'blocks': blocks,
            },
        )

    def get_my_team_time_off_lazy(self, body):
        state = body['view']['state']
        user_id = body['user']['id']
        team_id = self.team_management.get_team_id_by_user_id(user_id)
        member_filter_user_id = self.leave_lookup.get_value_from_state(
            state, 'team_timeoff_user_filter', extra_field='selected_user',
            block_id='team_timeoff_filter',
        )
        leave_type = self.leave_lookup.get_value_from_state(
            state, 'team_timeoff_type_filter', extra_field='selected_option.value',
            block_id='team_timeoff_filter',
        )
        start_date = self.leave_lookup.get_value_from_state(
            state, 'team_timeoff_start_filter', extra_field='selected_date',
            block_id='team_timeoff_filter',
        )
        end_date = self.leave_lookup.get_value_from_state(
            state, 'team_timeoff_end_filter', extra_field='selected_date',
            block_id='team_timeoff_filter',
        )
        blocks = self.leave_lookup.get_my_team_off_filter_blocks(
            team_id=team_id,
            user_id=member_filter_user_id, start_date=start_date, end_date=end_date,
            leave_type=leave_type,
        )

        self.client.views_publish(
            user_id=user_id, view={
                'type': 'home',
                'blocks': blocks,
            },
        )
