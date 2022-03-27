from __future__ import annotations

import json

from slack_bolt import App
from slack_sdk import WebClient

from application.handlers.bot.base_management import BaseManagement


class LeaveLookup(BaseManagement):
    def __init__(
            self, app: App, client: WebClient,
    ):
        super().__init__(app, client)
        app.command('/ooo-today')(ack=self.respond_to_slack_within_3_seconds, lazy=[self.trigger_today_ooo_command])

    @staticmethod
    def respond_to_slack_within_3_seconds(ack):
        ack()

    def trigger_today_ooo_command(self, body, respond):
        user_id = body.get('user_id') or body['user']['id']
        team_id = self.get_team_id_by_user_id(user_id)
        statuses = [
            self.constant.LEAVE_REQUEST_STATUS_APPROVED,
            self.constant.LEAVE_REQUEST_STATUS_WAIT,
        ]
        attachments = self.build_response_today_ooo(statuses, team_id)

        if attachments:
            text = 'As your request, Here is the list of users in your team OOO today'
        else:
            text = 'Sorry but nobody in your team is OOO today'
        if body.get('response_url'):
            return respond(
                response_type='ephemeral',
                text=text,
                attachments=attachments,
            )
        return self.client.chat_postMessage(
            channel=user_id,
            text=text,
            attachments=attachments,
        )

    def today_ooo_schedule(self):
        statuses = [
            self.constant.LEAVE_REQUEST_STATUS_APPROVED,
            self.constant.LEAVE_REQUEST_STATUS_WAIT,
        ]
        teams = self.team_db_handler.get_all_teams()
        for team in teams:
            attachments = self.build_response_today_ooo(statuses, team_id=team.id)
            if attachments:
                text = f'Hey, the following users (team {team.name}) are OOO today'
            else:
                text = f'Huray!, Nobody (team {team.name}) is OOO today'
            self.client.chat_postMessage(
                channel=team.announcement_channel_id,
                text=text,
                attachments=attachments,
            )

    def build_response_today_ooo(self, statuses, team_id=None):
        today_ooo_leaves = self.leave_register_db_handler.get_today_ooo(statuses, team_id)
        attachments = []
        if not today_ooo_leaves:
            return attachments
        for leave in today_ooo_leaves:
            attachments.append(
                json.loads(
                    self.block_kit.ooo_attachment(
                        username=leave.username,
                        leave_type=f'{self.constant.EMOJI_MAPPING[leave.leave_type]} {leave.leave_type}',
                        status=f'{self.constant.EMOJI_MAPPING[leave.status]} {leave.status}',
                        start_date=leave.start_date,
                        end_date=leave.end_date,
                    ),
                ),
            )
        return attachments

    def get_my_time_off_filter_blocks(self, user_id, start_date, end_date, leave_type, statuses):
        user_leave_rows = self.leave_register_db_handler.get_leaves(
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
            leave_type=leave_type,
            statuses=statuses,
        )
        user_leaves = self.build_leave_display_list(user_leave_rows)
        blocks = json.loads(
            self.block_kit.all_your_time_off_blocks(
                user_leaves=user_leaves,
            ),
        )
        return blocks

    def get_my_team_off_filter_blocks(self, team_id, user_id=None, start_date=None, end_date=None, leave_type=None):
        user_leave_rows = self.leave_register_db_handler.get_leaves(
            team_id=team_id,
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
            leave_type=leave_type,

        )
        user_leaves = self.build_leave_display_list(user_leave_rows, is_get_slack_user_info=True)
        blocks = json.loads(
            self.block_kit.all_your_team_time_off_blocks(
                user_leaves=user_leaves,
            ),
        )
        return blocks
