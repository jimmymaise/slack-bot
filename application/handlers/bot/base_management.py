from __future__ import annotations

import datetime
from contextlib import suppress

from slack_sdk import WebClient

from application.handlers.bot.block_template_handler import BlockTemplateHandler
from application.handlers.database.holiday_groups_db_handler import HolidayGroupsDBHandler
from application.handlers.database.holidays_db_handler import HolidaysDBHandler
from application.handlers.database.leave_registry_db_handler import LeaveRegistryDBHandler
from application.handlers.database.leave_type_handler import LeaveTypeDBHandler
from application.handlers.database.must_read_db_handler import MustReadDBHandler
from application.handlers.database.team_db_handler import TeamDBHandler
from application.handlers.database.team_member_db_handler import TeamMemberDBHandler
from application.handlers.database.weekdays_db_handler import WeekdaysDBHandler
from application.utils.cache import LambdaCache
from application.utils.constant import Constant
from application.utils.logger import Logger


class BaseManagement:
    def __init__(self, app, client: WebClient):
        self.app = app
        self.client = client
        self.logger = Logger.get_logger()

        self.team_member_db_handler = TeamMemberDBHandler()
        self.leave_register_db_handler = LeaveRegistryDBHandler()
        self.leave_type_db_handler = LeaveTypeDBHandler()
        self.must_read_db_handler = MustReadDBHandler()
        self.team_db_handler = TeamDBHandler()
        self.holidays_handler = HolidaysDBHandler()
        self.holiday_groups_handler = HolidayGroupsDBHandler()
        self.weekdays_handler = WeekdaysDBHandler()

        self.constant = Constant
        self.block_kit = BlockTemplateHandler(self.constant.BLOCK_TEMPLATE_PATH).get_object_templates()
        self.get_leave_types = self.leave_type_db_handler.get_all_leave_types_from_cache
        self.get_leave_type_detail_from_cache = self.leave_type_db_handler.get_leave_type_detail_from_cache

    @staticmethod
    def respond_to_slack_within_3_seconds(ack):
        ack()

    def chat_delete_message(self, channel, ts):
        with suppress(Exception):
            self.client.chat_delete(channel=channel, ts=ts)

    def send_direct_message_to_multiple_slack_users(self, user_ids, text, blocks=None):
        ts = None
        for user_id in user_ids:
            res = self.client.chat_postMessage(
                channel=user_id,
                text=text,
                blocks=blocks,
            )
            if not ts:
                ts = res['ts']

        return ts

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

    def get_username_by_user_id(self, user_id):
        user_name = LambdaCache.get_cache(f'slack_cache_{user_id}_user_name', False)
        if user_name:
            return user_name

        user_info = self.client.users_info(user=user_id)
        user_name = user_info.get('user').get('real_name')
        LambdaCache.set_cache(f'slack_cache_{user_id}_user_name', user_name)
        return user_name

    def get_slack_users_by_user_ids(self, user_ids):
        return [self.get_slack_user_by_user_id(user_id) for user_id in user_ids]

    def get_slack_user_by_user_id(self, user_id):
        return self.client.users_info(user=user_id).data['user']

    def get_today_date_str(self):
        return self.convert_date_obj_to_date_str(datetime.datetime.now())

    def convert_date_obj_to_date_str(self, date: datetime.date):
        return date.strftime(self.constant.DATE_FORMAT)

    def convert_date_str_to_date_obj(self, date_str: str):
        return datetime.datetime.strptime(date_str, self.constant.DATE_FORMAT)

    @staticmethod
    def get_today_date_time_obj():
        return datetime.datetime.now()

    @staticmethod
    def get_today_date_obj():
        return datetime.datetime.now().date()

    @staticmethod
    def get_value_from_state(state, name, extra_field=None, block_id=None):
        if not state:
            return None
        try:
            values = state['values'][block_id] if block_id else state['values']
            value = values[name][f'{name}_value'] if values[name].get(f'{name}_value') else values[name]
            extra_field_list = extra_field.split('.')
            for field in extra_field_list:
                value = value[field]
        except KeyError:
            return None
        return value

    def build_leave_display_list(self, user_leave_rows, is_get_slack_user_info=False):
        user_leaves = []
        for leave_row in user_leave_rows:
            is_past_leave = leave_row.end_date < self.get_today_date_obj()
            allowed_user_leave_actions = []
            if not is_past_leave or leave_row.status == self.constant.LEAVE_REQUEST_STATUS_WAIT:
                allowed_user_leave_actions = ['edit', 'cancel']
            user_leave = {
                'username': leave_row.username,
                'user_id': leave_row.user_id,
                'start_date': leave_row.start_date,
                'end_date': leave_row.end_date,
                'type_icon': self.get_leave_type_detail_from_cache(leave_row.leave_type)['icon'],
                'duration': f"{leave_row.start_date.strftime('%A, %B, %d, %Y')} "
                            f"to {leave_row.end_date.strftime('%A, %B, %d, %Y')}",
                'status_icon': self.constant.EMOJI_MAPPING.get(leave_row.status, ''),
                'reason': leave_row.reason,
                'type': leave_row.leave_type,
                'status': leave_row.status,
                'id': leave_row.id,
                'allowed_user_leave_actions': allowed_user_leave_actions,
            }
            if is_get_slack_user_info:
                user_leave['user'] = self.get_slack_user_by_user_id(user_id=leave_row.user_id)

            user_leaves.append(user_leave)
        return user_leaves

    def get_tagged_users_from_message(self, message_event):
        message_block = message_event['blocks'][0]
        tagged_users = []
        for element in message_block['elements'][0]['elements']:
            if element['type'] == 'user':
                tagged_users.append(element['user_id'])
            elif element['type'] == 'usergroup':
                tagged_users += self.client.usergroups_users_list(usergroup=element['usergroup_id'])['users']
            elif element['type'] == 'broadcast' and element['range'] == 'channel':
                tagged_users += \
                    self.client.conversations_members(channel=message_event['channel'])['members']

        tagged_users = list(set(tagged_users))
        return tagged_users

    def get_users_make_reaction_to_message(self, channel, message_ts, reaction_name):
        reaction_info = self.client.reactions_get(channel=channel, timestamp=message_ts, reaction_name=reaction_name)
        reactions = reaction_info['message'].get('reactions', [])
        for reaction in reactions:
            if reaction['name'] == reaction_name:
                return reaction['users']
        return []

    def get_one_slack_message(self, channel_id, message_ts):
        result = self.client.conversations_history(
            channel=channel_id,
            inclusive=True,
            oldest=message_ts,
            limit=1,
        )
        if not result['messages']:
            result = self.client.conversations_replies(
                channel=channel_id,
                inclusive=True,
                ts=message_ts,
                limit=1,
            )

        message = result['messages'][0]
        return message
