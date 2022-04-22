from __future__ import annotations

import json
import re
from datetime import datetime

from slack_bolt import App
from slack_sdk import WebClient

from application.handlers.bot.base_management import BaseManagement


class MustReadMessage(BaseManagement):
    def __init__(
            self, app: App, client: WebClient,
    ):
        super().__init__(app, client)
        self.client = client
        app.event('message')(
            ack=self.respond_to_slack_within_3_seconds,
            lazy=[self.add_must_read_message_lazy],
        )

        app.command('/must-read-not-completed')(
            ack=self.respond_to_slack_within_3_seconds,
            lazy=[self.get_my_must_read_messages_not_completed_read],
        )

    def add_must_read_message_lazy(self, body, context, say):
        event_sub_type = body['event'].get('subtype')
        is_edited_message = event_sub_type == 'message_changed'
        if is_edited_message:
            message_event = body['event']['message']
            message = body['event']['message']['text']
            message_ts = body['event']['message']['ts']
            user_id = body['event']['message']['user']

        else:
            message_event = body['event']
            message = body['event']['text']
            message_ts = body['event']['ts']
            user_id = body['event']['user']

        if '#must-read' not in message:
            return
        is_already_must_read = is_edited_message and bool(
            self.must_read_db_handler.get_must_read_messages(
                author_user_id=user_id,
                message_ts=message_ts,
            ),
        )
        if is_already_must_read:
            return

        channel = body['event']['channel']
        if not message.startswith('#must-read'):
            return self.client.chat_postEphemeral(
                channel=channel,
                user=user_id,
                text='You might try to create must read message but '
                     'forgot to put #must-read at the beginning of message. '
                     'Please edit it and create again if you want to do so',
            )

        tagged_users = self.get_tagged_users_from_message(message_event)

        normalize_content = re.sub(r"""<.+?>""", '', message).replace('\n', '').replace('#must-read', '')
        short_content: str = normalize_content[0:100]

        if not tagged_users:
            return self.client.chat_postEphemeral(
                channel=channel,
                user=user_id,
                text='You might try to create must read message but forgot to tag anyone.'
                     'Please edit it and create again if you want to do so',

            )

        permalink = self.app.client.chat_getPermalink(message_ts=message_ts, channel=channel)[
            'permalink'
        ]
        self.must_read_db_handler.add_must_read_messages(
            message_ts=message_ts,
            author_user_id=user_id,
            status=self.constant.MUST_READ_STATUS_IN_PROGRESS,
            short_content=short_content,
            permalink=permalink,
            channel=channel,
        )

        for tagged_user_id in tagged_users:
            self.client.chat_postMessage(
                channel=tagged_user_id,
                blocks=json.loads(
                    self.block_kit.send_dm_to_inform_newly_created_must_read_message_blocks(
                        permalink=permalink,
                        short_content=short_content,
                        reaction=self.constant.ACK_EMOJI,
                        tagged_user_id=tagged_user_id,
                    ),
                ),
            )
        return self.client.chat_postEphemeral(
            channel=channel,
            user=user_id,
            text='You just made a must read message and I have informed it '
                 f'to the following tagged users {",".join([f"<@{tagged_user}>" for tagged_user in tagged_users])}.'
                 f'You can type the command `/must-read-not-completed ` to check its status',

        )

    def get_my_must_read_messages_not_completed_read(self, body, context, respond):
        must_read_message_rows = self.must_read_db_handler.get_must_read_messages(
            statuses=[self.constant.MUST_READ_STATUS_IN_PROGRESS],
            author_user_id=context.user_id,
        )
        my_message_objs = []

        for must_read_message_row in must_read_message_rows:
            message_ts = must_read_message_row.message_ts.split('ts_')[1]
            tagged_users, reacted_users = self._get_tagged_users_ack_user_from_message(
                message_ts,
                must_read_message_row.channel,
            )
            posted_date = datetime.fromtimestamp(float(message_ts)).strftime('%b %d at %H:%M')
            not_read_user_ids = list(set(tagged_users) - set(reacted_users))
            if not not_read_user_ids:
                self.must_read_db_handler.update_item_with_retry(
                    _id=must_read_message_row.id,
                    update_data={
                        'status': self.constant.MUST_READ_STATUS_COMPLETED,
                    },
                )
                continue
            my_message_obj = {
                'message_ts': message_ts,
                'short_content': must_read_message_row.short_content,
                'permalink': must_read_message_row.permalink,
                'channel': must_read_message_row.channel,
                'posted_date': posted_date,
                'not_read_user_ids': list(set(tagged_users) - set(reacted_users)),
            }
            my_message_objs.append(my_message_obj)

        if not my_message_objs:
            return respond(
                response_type='ephemeral',
                text='Congratulation, your teammates have read all your must read message!',
            )
        return respond(
            response_type='ephemeral',
            blocks=json.loads(
                self.block_kit.get_my_must_read_message_not_completed_read(
                    my_message_objs=my_message_objs,
                    reaction=self.constant.ACK_EMOJI,
                ),
            ),
        )

    def remind_must_read_message(self):
        remind_dict = {}
        must_read_message_rows = self.must_read_db_handler.get_must_read_messages(
            statuses=[self.constant.MUST_READ_STATUS_IN_PROGRESS],
        )
        for must_read_message_row in must_read_message_rows:
            message_ts = must_read_message_row.message_ts.split('ts_')[1]
            tagged_users, reacted_users = self._get_tagged_users_ack_user_from_message(
                message_ts,
                must_read_message_row.channel,
            )
            posted_date = datetime.fromtimestamp(float(message_ts)).strftime('%b %d at %H:%M')
            remind_message_obj = {
                'author_user_id': must_read_message_row.author_user_id,
                'message_ts': message_ts,
                'short_content': must_read_message_row.short_content,
                'permalink': must_read_message_row.permalink,
                'channel': must_read_message_row.channel,
                'posted_date': posted_date,
            }
            reminder_users = list(set(tagged_users) - set(reacted_users))
            if not reminder_users:
                self.must_read_db_handler.update_item_with_retry(
                    _id=must_read_message_row.id,
                    update_data={
                        'status': self.constant.MUST_READ_STATUS_COMPLETED,
                    },
                )
            for reminder_user in reminder_users:
                remind_dict[reminder_user] = remind_dict.get(reminder_user, [])
                remind_dict[reminder_user].append(remind_message_obj)

        for reminder_user_id, remind_message_objs in remind_dict.items():
            self.client.chat_postMessage(
                channel=reminder_user_id,
                blocks=json.loads(
                    self.block_kit.send_dm_to_remind_must_read_messages(
                        reminder_user_id=reminder_user_id,
                        remind_message_objs=remind_message_objs,
                        reaction=self.constant.ACK_EMOJI,
                    ),
                ),
            )

    def _get_tagged_users_ack_user_from_message(self, message_ts, channel):

        message_detail = self.get_one_slack_message(
            channel_id=channel,
            message_ts=message_ts,
        )
        message_detail['channel'] = channel

        tagged_users = self.get_tagged_users_from_message(message_detail)
        reacted_users = self.get_users_make_reaction_to_message(
            channel=channel,
            reaction_name=self.constant.ACK_EMOJI,
            message_ts=message_ts,
        )
        return tagged_users, reacted_users
