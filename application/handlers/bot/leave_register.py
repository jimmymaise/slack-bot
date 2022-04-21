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
            ack=self.respond_to_slack_within_3_seconds, lazy=[self.take_action_on_leave_from_action_block],
        )
        app.block_action({'block_id': 'approve_reject_vacation', 'action_id': 'reject'})(
            ack=self.respond_to_slack_within_3_seconds,
            lazy=[self.take_action_on_leave_from_action_block],
        )

    def trigger_request_leave_command(self, client, body, ack):
        leave_types = self.get_leave_types()
        client.views_open(
            trigger_id=body.get('trigger_id'),
            view=json.loads(
                self.block_kit.leave_input_view(
                    callback_id='leave_input_view',
                    leave_types=leave_types,
                ),
            ),
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
        # todo: validate start_date and end_date not weekday
        if errors:
            return ack(
                response_action='errors',
                errors=errors,
            )
        private_metadata = json.loads(body['view']['private_metadata'])
        private_metadata.update({
            'reason_of_leave': reason_of_leave,
            'leave_type': leave_type,
            'start_date_str': start_date_str,
            'end_date_str': end_date_str,

        })
        leave_id = private_metadata.get('leave_id')
        private_metadata_json_str = json.dumps(private_metadata)
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
                statuses=[self.constant.LEAVE_REQUEST_STATUS_APPROVED, self.constant.LEAVE_REQUEST_STATUS_WAIT],
            )
            is_query_db = True
        for overlap_leave in overlap_leaves:
            if not leave_id or leave_id != str(overlap_leave.id):
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
        leave_confirmation_view['private_metadata'] = private_metadata_json_str

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
        leave_id = private_metadata.get('leave_id')
        team_id = self.get_team_id_by_user_id(user_id=user_id)
        number_of_leave_days = len(
            self.get_working_days_from_date_range_by_team_id(
                team_id=team_id,
                start_date_str=start_date_str,
                end_date_str=end_date_str,
            ),
        )

        old_leave_message_ts = private_metadata.get('leave_message_ts')
        is_update_leave = bool(leave_id)

        manager_ids = [
            manager.user_id for manager in
            self.team_member_db_handler.get_managers_by_user_id(user_id)
        ]

        if is_update_leave:
            self.leave_register_db_handler.update_a_leave(
                _id=private_metadata['leave_id'],
                update_data={
                    'start_date': start_date_str,
                    'end_date': end_date_str,
                    'reason': reason_of_leave,
                    'status': self.constant.LEAVE_REQUEST_STATUS_WAIT,
                    'number_of_leave_days': number_of_leave_days,
                },
            )
            manager_ask_for_approval_message = f'A time off request of *<{user_profile_url}|{user_name}>*' \
                                               f' has been updated'
            requester_confirm_message = 'You have just update a leave request.Please wait to manager approve'

            if old_leave_message_ts:
                for manager_user_id in manager_ids:
                    self.chat_delete_message(channel=manager_user_id, ts=old_leave_message_ts)
        else:
            leave_id = self.leave_register_db_handler.add_a_leave(
                leave_type, reason_of_leave, user_name, user_id, start_date_str,
                end_date_str, number_of_leave_days,

            )
            manager_ask_for_approval_message = f'New time off request from *<{user_profile_url}|{user_name}>*' \
                                               f' has just arrived. Please approve or decline:'
            requester_confirm_message = 'You have sent a new vacation request.Please wait to manager approve'
        leave_type_detail = self.get_leave_type_detail_from_cache(leave_type)
        channel_message_block = self.block_kit.new_vacation_request_channel_message_blocks(
            user_id=user_id,
            user_name=user_name,
            reason_of_leave=reason_of_leave,
            leave_type=f'{leave_type_detail["icon"]} {leave_type}',
            leave_id=leave_id,
            start_date=start_date,
            end_date=end_date,
            message=manager_ask_for_approval_message,
            number_of_leave_days=number_of_leave_days,

        )

        message_ts = self.send_direct_message_to_multiple_slack_users(
            user_ids=manager_ids,
            text=manager_ask_for_approval_message,
            blocks=channel_message_block,
        )

        logger.info(body)
        leave_type_detail = self.get_leave_type_detail_from_cache(leave_type)

        confirm_requester_message_block = json.loads(
            self.block_kit.vacation_request_confirm_requester_message_blocks(
                leave_type=f'{leave_type_detail["icon"]} {leave_type}',
                leave_id=leave_id,
                start_date=start_date,
                end_date=end_date,
                reason_of_leave=reason_of_leave,
                number_of_leave_days=number_of_leave_days,

            ),
        )
        self.leave_register_db_handler.update_item_with_retry(
            _id=leave_id,
            update_data={'message_ts': f'ts_{message_ts}'},
        )
        self.client.chat_postMessage(
            channel=user_id,
            text=requester_confirm_message,
            blocks=confirm_requester_message_block,
        )

    def take_action_on_leave_from_action_block(self, body, ack):
        action = body.get('actions')[0].get('text').get('text')
        leave_id = body.get('actions')[0].get('value')
        message_ts = body.get('container', {}).get('message_ts')
        changed_by_user_id = body['user']['id']
        self._take_action_on_leave(
            leave_id=leave_id,
            message_ts=message_ts,
            action=action,
            changed_by_user_id=changed_by_user_id,
        )

    def take_action_on_leave_from_overflow_block(self, body, ack):
        action, leave_id = body['actions'][0]['selected_option']['value'].split(',')
        changed_by_user_id = body['user']['id']

        if action == self.constant.LEAVE_REQUEST_ACTION_EDIT:
            self.open_edit_leave_view(
                leave_id=leave_id,
                trigger_id=body['trigger_id'],
            )
        else:
            self._take_action_on_leave(
                leave_id=leave_id,
                message_ts=None,
                action=action,
                changed_by_user_id=changed_by_user_id,
            )

    def open_edit_leave_view(self, leave_id, trigger_id):
        leave = self.leave_register_db_handler.find_item_by_id(
            _id=leave_id,
        )
        private_metadata = json.dumps({
            'leave_id': leave_id,
            'leave_message_ts': leave.message_ts.split('ts_')[1] if leave.message_ts else None,
        })
        leave_input_view = json.loads(
            self.block_kit.leave_input_view(
                callback_id='leave_input_view',
                leave=leave,
                leave_types=self.get_leave_types(),
            ),
        )
        leave_input_view['private_metadata'] = private_metadata
        self.client.views_open(
            trigger_id=trigger_id,
            view=leave_input_view,
        )

    def _take_action_on_leave(self, leave_id, changed_by_user_id, action, message_ts=None):

        status = self.constant.LEAVE_DECISION_TO_STATUS[action]
        leave = self.leave_register_db_handler.find_item_by_id(_id=leave_id)
        if not message_ts:
            message_ts = leave.message_ts

        changed_by_user_id = changed_by_user_id
        requester_user_id = leave.user_id
        requester_name = self.get_username_by_user_id(user_id=leave.user_id)
        changed_by_name = self.get_username_by_user_id(user_id=changed_by_user_id)

        self.leave_register_db_handler.change_leave_status(
            leave_id=leave_id,
            updated_by=changed_by_name,
            status=status,
        )

        # Delete responded message
        managers = self.team_member_db_handler.get_managers_by_user_id(user_id=requester_user_id)
        manager_ids = [manager.user_id for manager in managers]
        if message_ts:
            for manager in managers:
                self.client.chat_delete(channel=manager.user_id, ts=message_ts)
        if action == self.constant.LEAVE_REQUEST_ACTION_APPROVE:
            manager_message = self.constant.APPROVE_MESSAGE_TO_MANAGER
            requester_message = self.constant.APPROVE_MESSAGE_TO_REQUESTER

        elif action == self.constant.LEAVE_REQUEST_ACTION_REJECT:
            manager_message = self.constant.REJECT_MESSAGE_TO_MANAGER
            requester_message = self.constant.REJECT_MESSAGE_TO_REQUESTER
        else:
            manager_message = self.constant.CANCEL_MESSAGE_TO_MANAGER
            requester_message = self.constant.CANCEL_MESSAGE_TO_REQUESTER

        self.client.chat_postMessage(
            channel=self.approval_channel,
            text=manager_message.format(
                leave_id=leave.id,
                start_date=leave.start_date,
                end_date=leave.end_date,
                requester_user_id=requester_user_id,
                requester_name=requester_name,
                changed_by_name=changed_by_name,
                changed_by_user_id=changed_by_user_id,

            ),
        )

        self.send_direct_message_to_multiple_slack_users(
            user_ids=manager_ids,
            text=manager_message.format(
                leave_id=leave.id,
                start_date=leave.start_date,
                end_date=leave.end_date,
                requester_user_id=leave.user_id,
                requester_name=requester_name,
                changed_by_name=changed_by_name,
                changed_by_user_id=changed_by_user_id,

            ),
        )
        self.client.chat_postMessage(
            channel=requester_user_id,
            text=requester_message.format(
                leave_id=leave.id,
                start_date=leave.start_date,
                end_date=leave.end_date,
                requester_user_id=leave.user_id,
                requester_name=requester_name,
                changed_by_name=changed_by_name,
                changed_by_user_id=changed_by_user_id,

            ),
        )
