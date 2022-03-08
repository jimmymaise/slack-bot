from __future__ import annotations

import datetime
import json

from slack_bolt import App
from slack_sdk import WebClient

from application.handlers.bot.block_template_handler import BlockTemplateHandler
from application.handlers.database.google_sheet import GoogleSheetDB
from application.handlers.database.leave_registry_db_handler import LeaveRegistryDBHandler
from application.utils.cache import LambdaCache
from application.utils.constant import Constant


class LeaveRegister:
    def __init__(
        self, app: App, client: WebClient, google_sheet_db: GoogleSheetDB,
        leave_register_sheet, approval_channel: str,
    ):
        self.app = app
        self.client = client
        self.google_sheet_db = google_sheet_db
        self.leave_register_sheet = leave_register_sheet
        self.approval_channel = approval_channel
        app.command('/vacation')(ack=self.respond_to_slack_within_3_seconds, lazy=[self.trigger_request_leave_command])
        app.view('leave_input_view')(self.get_leave_confirmation_view)
        app.view('leave_confirmation_view')(
            ack=lambda ack: ack(response_action='clear'),
            lazy=[self.handle_leave_request_submission],
        )

        app.block_action({'block_id': 'approve_reject_vacation', 'action_id': 'approve'})(
            ack=self.respond_to_slack_within_3_seconds, lazy=[self.approve_pto],
        )
        app.block_action({'block_id': 'approve_reject_vacation', 'action_id': 'reject'})(
            ack=self.respond_to_slack_within_3_seconds,
            lazy=[self.reject_pto],
        )
        self.block_kit = BlockTemplateHandler('./application/handlers/bot/block_templates').get_object_templates()

        self.leave_register_db_handler = LeaveRegistryDBHandler(
            google_sheet_db=google_sheet_db,
            leave_register_sheet=leave_register_sheet,
        )

    @staticmethod
    def respond_to_slack_within_3_seconds(ack):
        ack()

    def trigger_request_leave_command(self, client, body, ack):
        client.views_open(
            trigger_id=body.get('trigger_id'),
            view=json.loads(self.block_kit.leave_input_view(callback_id='leave_input_view')),
        )

    def _get_username_by_user_id(self, user_id):

        user_name = LambdaCache.get_cache(f'slack_cache_{user_id}_user_name', False)
        if user_name:
            return user_name

        user_info = self.client.users_info(user=user_id)
        user_name = user_info.get('user').get('real_name')
        LambdaCache.set_cache(f'slack_cache_{user_id}_user_name', user_name)
        return user_name

    def get_leave_confirmation_view(self, body, ack):
        errors = {}
        values = body.get('view').get('state').get('values')

        reason_of_leave = values.get('reason_of_leave').get('reason_for_leave').get('value')
        leave_type = values.get('leave_type').get('leave_type').get('selected_option').get('value')

        start_date_str = values.get('vacation_start_date').get('vacation_start_date_picker').get('selected_date')
        end_date_str = values.get('vacation_end_date').get('vacation_end_date_picker').get('selected_date')

        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d')
        if start_date > end_date:
            errors['vacation_start_date'] = "Start date can't be later than the end date"

            return ack(
                response_action='errors',
                errors=errors,
            )

        private_metadata = json.dumps({
            'reason_of_leave': reason_of_leave,
            'leave_type': leave_type,
            'start_date_str': start_date_str,
            'end_date_str': end_date_str,

        })
        user = body.get('user')
        user_id = user.get('id')
        user_name = self._get_username_by_user_id(user_id)
        user_overlap_leave_key = f'db_cache_{user_name}_{start_date_str}{end_date_str}_overlap_leave_key'
        overlap_leaves = []
        is_query_db = False

        if LambdaCache.is_exist_cache(user_overlap_leave_key):
            leave_overlap_value = LambdaCache.get_cache(user_overlap_leave_key)
            if leave_overlap_value:
                overlap_leaves.append(leave_overlap_value)
                print('Getting overlap leave from cache')
        else:
            overlap_leaves = self.leave_register_db_handler.get_overlap_leaves_by_date_ranges(
                user_name, start_date_str,
                end_date_str,
            )
            is_query_db = True
        for overlap_leave in overlap_leaves:
            errors['vacation_start_date'] = f'Oh no! You already have time off scheduled for these dates' \
                                            f' (leave id: {overlap_leave[0]}, from cache: {not is_query_db})'
            if is_query_db:
                LambdaCache.set_cache(user_overlap_leave_key, overlap_leave)
            return ack(
                response_action='errors',
                errors=errors,
            )
        leave_confirmation_view = self.block_kit.leave_confirmation_view(
            callback_id='leave_confirmation_view',
            leave_type=leave_type,
            start_date_str=start_date_str,
            end_date_str=end_date_str,
            reason_of_leave=reason_of_leave,
        )

        leave_confirmation_view = json.loads(leave_confirmation_view)
        leave_confirmation_view['private_metadata'] = private_metadata

        ack(
            response_action='push',
            view=leave_confirmation_view,
        )

    # Update the view on submission
    def handle_leave_request_submission(self, body, logger):
        workspace_domain = f"https://{self.client.team_info().get('team').get('domain')}.slack.com/team/"
        user = body.get('user')
        user_id = user.get('id')
        user_name = self._get_username_by_user_id(user_id)
        user_profile_url = workspace_domain + user_id

        private_metadata = json.loads(body['view']['private_metadata'])
        reason_of_leave = private_metadata['reason_of_leave']
        leave_type = private_metadata['leave_type']

        start_date_str = private_metadata['start_date_str']
        end_date_str = private_metadata['end_date_str']
        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d')

        leave_id = self.leave_register_db_handler.add_a_leave(
            leave_type, reason_of_leave, user_name, start_date_str,
            end_date_str,
        )
        channel_message_block = self.block_kit.new_vacation_request_channel_message_blocks(
            user_profile_url=user_profile_url,
            user_name=user_name,
            reason_of_leave=reason_of_leave,
            leave_type=leave_type,
            leave_id=leave_id,
            start_date=start_date,
            end_date=end_date,
        )
        self.client.chat_postMessage(
            channel=self.approval_channel,
            text=f'You have a new request:\n*<{user_profile_url}|{user_name} - New vacation request>*',
            blocks=channel_message_block,
        )

        logger.info(body)
        confirm_requester_message_block = json.loads(
            self.block_kit.vacation_request_confirm_requester_message_blocks(
                leave_type=leave_type,
                leave_id=leave_id,
                start_date=start_date,
                end_date=end_date,
                reason_of_leave=reason_of_leave,
            ),
        )
        self.client.chat_postMessage(
            channel=user_id,
            text='You have sent a new vacation request. '
                 'Please wait to manager approve',
            blocks=confirm_requester_message_block,
        )

    def approve_pto(self, ack, body, logger):
        self._process_leave_actions(body, ack)

    def reject_pto(self, ack, body, logger):
        self._process_leave_actions(body, ack)

    def _process_leave_actions(self, body, ack):
        container = body.get('container')
        message_ts = container.get('message_ts')
        channel_id = container.get('channel_id')
        decision = body.get('actions')[0].get('text').get('text')
        status = Constant.LEAVE_DECISION_TO_STATUS[decision]
        leave_id = body['message']['blocks'][2]['fields'][1]['text'].split(':*\n')[1].strip()
        start_date = body['message']['blocks'][3]['fields'][0]['text'].split(':*')[1].strip()
        end_date = body['message']['blocks'][3]['fields'][1]['text'].split(':*\n')[1].strip()
        # Manager info
        manager_id = body.get('user').get('id')
        manager_info = self.client.users_info(user=manager_id)

        manager_name = manager_info.get('user').get('real_name')
        # User info
        temp = body.get('message').get('blocks')[0].get('text').get('text')
        user_id = temp[temp.index('/U') + 1: temp.index('|')]
        user_info = self.client.users_info(user=user_id)
        user_name = user_info.get('user').get('real_name')

        self.leave_register_db_handler.change_leave_status(
            leave_id=leave_id,
            manager_name=manager_name,
            status=status,
        )

        # Delete responded message
        self.client.chat_delete(channel=channel_id, ts=message_ts)
        if decision == Constant.LEAVE_REQUEST_ACTION_APPROVE:

            self.client.chat_postMessage(
                channel=self.approval_channel,
                text=f':tada:Leave Request for {user_name} (From {start_date} To {end_date}) '
                     f'has been approved by {manager_name}. Leave Id: {leave_id}',
            )
            self.client.chat_postMessage(
                channel=user_id,
                text=f':tada:Your leave request (From {start_date} to {end_date}) '
                     f'has been approved by {manager_name}:smiley: . Leave Id: {leave_id}',
            )
        else:
            self.client.chat_postMessage(
                channel=self.approval_channel,
                text=f':x:Leave Request for {user_name} (From {start_date} To {end_date}) '
                     f'has been rejected by {manager_name} . Leave Id: {leave_id}',
            )
            self.client.chat_postMessage(
                channel=user_id,
                text=f':x:Your leave request (From {start_date} To {end_date}) has been rejected by {manager_name}'
                     f' :cry: . Leave Id: {leave_id}',
            )

        ack()
