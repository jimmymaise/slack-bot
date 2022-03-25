from __future__ import annotations

import datetime
import json

from slack_bolt import App
from slack_sdk import WebClient

from application.handlers.bot.base_management import BaseManagement
from application.utils.cache import LambdaCache


class LeaveRegister(BaseManagement):
    def __init__(
            self, app: App, client: WebClient, approval_channel,
    ):
        super().__init__(app, client)
        self.approval_channel = approval_channel
        app.command('/vacation')(ack=self.respond_to_slack_within_3_seconds, lazy=[self.trigger_request_leave_command])
        app.view('leave_input_view')(self.get_leave_confirmation_view)
        app.view('leave_confirmation_view')(
            ack=lambda ack: ack(response_action='clear'),
            lazy=[self.handle_leave_request_submission],
        )

        app.block_action({'block_id': 'approve_reject_vacation', 'action_id': 'approve'})(
            ack=self.respond_to_slack_within_3_seconds, lazy=[self.process_leave_actions],
        )
        app.block_action({'block_id': 'approve_reject_vacation', 'action_id': 'reject'})(
            ack=self.respond_to_slack_within_3_seconds,
            lazy=[self.process_leave_actions],
        )

    @staticmethod
    def respond_to_slack_within_3_seconds(ack):
        ack()

    def trigger_request_leave_command(self, client, body, ack):
        client.views_open(
            trigger_id=body.get('trigger_id'),
            view=json.loads(self.block_kit.leave_input_view(callback_id='leave_input_view')),
        )

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
        user_id = body['user']['id']
        user_overlap_leave_key = f'db_cache_{user_id}_{start_date_str}{end_date_str}_overlap_leave_key'
        overlap_leaves = []
        is_query_db = False

        if LambdaCache.is_exist_cache(user_overlap_leave_key):
            leave_overlap_value = LambdaCache.get_cache(user_overlap_leave_key)
            if leave_overlap_value:
                overlap_leaves.append(leave_overlap_value)
                self.logger.info('Getting overlap leave from cache')
        else:
            overlap_leaves = self.leave_register_db_handler.get_leaves(
                user_id=user_id, start_date=start_date_str,
                end_date=end_date_str,
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
        user_id = body['user']['id']
        user_name = self.get_username_by_user_id(user_id)
        user_profile_url = workspace_domain + user_id

        private_metadata = json.loads(body['view']['private_metadata'])
        reason_of_leave = private_metadata['reason_of_leave']
        leave_type = private_metadata['leave_type']

        start_date_str = private_metadata['start_date_str']
        end_date_str = private_metadata['end_date_str']
        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d')

        leave_id = self.leave_register_db_handler.add_a_leave(
            leave_type, reason_of_leave, user_name, user_id, start_date_str,
            end_date_str,
        )
        channel_message_block = self.block_kit.new_vacation_request_channel_message_blocks(
            user_id=user_id,
            user_name=user_name,
            reason_of_leave=reason_of_leave,
            leave_type=f'{self.constant.EMOJI_MAPPING[leave_type]} {leave_type}',
            leave_id=leave_id,
            start_date=start_date,
            end_date=end_date,
        )
        manager_ids = [
            manager.user_id for manager in
            self.team_member_db_handler.get_managers_by_user_id(user_id)
        ]
        message_ts = self.send_direct_message_to_multiple_slack_users(
            user_ids=manager_ids,
            text=f'You have a new request:\n*<{user_profile_url}|{user_name} - New vacation request>*',
            blocks=channel_message_block,
        )

        logger.info(body)
        confirm_requester_message_block = json.loads(
            self.block_kit.vacation_request_confirm_requester_message_blocks(
                leave_type=f'{self.constant.EMOJI_MAPPING[leave_type]} {leave_type}',
                leave_id=leave_id,
                start_date=start_date,
                end_date=end_date,
                reason_of_leave=reason_of_leave,
            ),
        )
        self.leave_register_db_handler.update_item_with_retry(
            _id=leave_id,
            update_data={'message_ts': f'ts_{message_ts}'},
        )
        self.client.chat_postMessage(
            channel=user_id,
            text='You have sent a new vacation request. '
                 'Please wait to manager approve',
            blocks=confirm_requester_message_block,
        )

    def process_leave_actions(self, body, ack):
        decision = body.get('actions')[0].get('text').get('text')
        leave_id = body.get('actions')[0].get('value')
        status = self.constant.LEAVE_DECISION_TO_STATUS[decision]
        leave = self.leave_register_db_handler.find_item_by_id(_id=leave_id)
        message_ts = leave.message_ts.split('ts_')[1] if leave.message_ts else body.get('container').get(
            'message_ts',
        )
        start_date = leave.start_date
        end_date = leave.end_date
        # Manager info
        manager_id = body.get('user').get('id')
        manager_info = self.client.users_info(user=manager_id)

        manager_name = manager_info.get('user').get('real_name')
        # User info
        user_id = leave.user_id
        user_info = self.client.users_info(user=user_id)
        user_name = user_info.get('user').get('real_name')

        self.leave_register_db_handler.change_leave_status(
            leave_id=leave_id,
            manager_name=manager_name,
            status=status,
        )

        # Delete responded message
        managers = self.team_member_db_handler.get_managers_by_user_id(user_id=user_id)
        manager_ids = [manager.user_id for manager in managers]
        if message_ts:
            for manager in managers:
                self.client.chat_delete(channel=manager.user_id, ts=message_ts)
        if decision == self.constant.LEAVE_REQUEST_ACTION_APPROVE:

            self.client.chat_postMessage(
                channel=self.approval_channel,
                text=f':tada:Leave Request for {user_name}<@{user_id}>  (From {start_date} To {end_date}) '
                     f'has been approved by {manager_name} <@{manager_id}> . Leave Id: {leave_id}',
            )

            self.send_direct_message_to_multiple_slack_users(
                user_ids=manager_ids,
                text=f':tada:Leave Request for {user_name}<@{user_id}>  (From {start_date} To {end_date}) '
                     f'has been approved by {manager_name} <@{manager_id}> .. Leave Id: {leave_id}',
            )
            self.client.chat_postMessage(
                channel=user_id,
                text=f':tada:Your leave request (From {start_date} to {end_date}) '
                     f'has been approved by {manager_name} <@{manager_id}> :smiley: . Leave Id: {leave_id}',
            )
        else:

            self.send_direct_message_to_multiple_slack_users(
                user_ids=manager_ids,
                text=f':tada:Leave Request for {user_name}<@{user_id}>  (From {start_date} To {end_date}) '
                     f'has been approved by {manager_name} <@{manager_id}> . Leave Id: {leave_id}',
            )
            self.client.chat_postMessage(
                channel=self.approval_channel,
                text=f':x:Leave Request for  {user_name}<@{user_id}>  (From {start_date} To {end_date}) '
                     f'has been rejected by {manager_name} <@{manager_id}>  . Leave Id: {leave_id}',
            )
            self.client.chat_postMessage(
                channel=user_id,
                text=f':x:Your leave request (From {start_date} To {end_date}) '
                     f'has been rejected by {manager_name} <@{manager_id}> :cry: . Leave Id: {leave_id}',
            )

        ack()
