import json

from slack_bolt import App
from slack_sdk import WebClient

from application.handlers.bot.block_template_handler import BlockTemplateHandler
from application.handlers.database.google_sheet import GoogleSheetDB
from application.handlers.database.leave_registry_db_handler import LeaveRegistryDBHandler
from application.utils.constant import Constant


class LeaveLookup:
    def __init__(self, app: App, client: WebClient, google_sheet_db: GoogleSheetDB,
                 leave_register_sheet):
        self.app = app
        self.client = client
        self.block_kit = BlockTemplateHandler('./application/handlers/bot/block_templates').get_object_templates()
        self.google_sheet_db = google_sheet_db
        self.leave_register_sheet = leave_register_sheet
        app.command('/ooo-today')(ack=self.respond_to_slack_within_3_seconds, lazy=[self.trigger_today_ooo_command])

        self.leave_register_db_handler = LeaveRegistryDBHandler(google_sheet_db=google_sheet_db,
                                                                leave_register_sheet=leave_register_sheet
                                                                )

    @staticmethod
    def respond_to_slack_within_3_seconds(ack):
        ack()

    def trigger_today_ooo_command(self, client, body, ack, respond):
        statuses = [Constant.LEAVE_REQUEST_STATUS_APPROVED,
                    Constant.LEAVE_REQUEST_STATUS_WAIT]
        respond(response_type="in_channel",
                text="As your request, Here is the list of users OOO today",
                attachments=self.build_response_today_ooo(statuses)
                )

    def today_ooo_schedule(self, channel):
        statuses = [Constant.LEAVE_REQUEST_STATUS_APPROVED,
                    Constant.LEAVE_REQUEST_STATUS_WAIT]
        self.client.chat_postMessage(channel=channel,
                                     text="Hey, the following users are OOO today",
                                     attachments=self.build_response_today_ooo(statuses)
                                     )

    def build_response_today_ooo(self, statuses):
        today_ooo_items = self.leave_register_db_handler.get_today_ooo(statuses)
        attachments = []
        item_keys = [column[0] for column in today_ooo_items.description]
        for item_values in today_ooo_items:
            item_dict = dict(zip(item_keys, item_values))
            attachments.append(json.loads(self.block_kit.ooo_attachment(
                username=item_dict['username'],
                leave_type=f"{Constant.EMOJI_MAPPING[item_dict['leave_type']]} {item_dict['leave_type']}",
                status=f"{Constant.EMOJI_MAPPING[item_dict['status']]} {item_dict['status']}",
                start_date=item_dict['start_date'],
                end_date=item_dict['end_date']
            )))
        return attachments
