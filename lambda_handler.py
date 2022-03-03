import os

from slack_bolt import App
from slack_bolt.adapter.aws_lambda import SlackRequestHandler
from slack_sdk import WebClient

from application.handlers.bot.home_tab import HomeTab
from application.handlers.bot.leave_lookup import LeaveLookup
from application.handlers.bot.leave_register import LeaveRegister
from application.handlers.database.google_sheet import GoogleSheetDB
from application.utils.constant import Constant

client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))
bolt_app = App(token=os.environ.get("SLACK_BOT_TOKEN"),
               signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
               url_verification_enabled=True,
               request_verification_enabled=False,
               process_before_response=True
               )

google_sheet_db = GoogleSheetDB(
    service_account_file_content=os.getenv('GOOGLE_SERVICE_BASE64_FILE_CONTENT'), is_encode_base_64=True)

LeaveRegister(bolt_app, client, google_sheet_db,
              leave_register_sheet=os.getenv('LEAVE_REGISTER_SHEET'),
              approval_channel=os.getenv('MANAGER_LEAVE_APPROVAL_CHANNEL'))
leave_lookup = LeaveLookup(bolt_app, client, google_sheet_db, os.getenv('LEAVE_REGISTER_SHEET'))

HomeTab(bolt_app, client)


def handler(event, context):
    schedule_event = event.get('lambda_trigger_event')
    if schedule_event:
        print(schedule_event)
        schedule_process(schedule_event)
    slack_handler = SlackRequestHandler(app=bolt_app)
    return slack_handler.handle(event, context)


def schedule_process(schedule_event):
    if schedule_event == Constant.SCHEDULER_OOO_TODAY:
        leave_lookup.today_ooo_schedule(os.getenv('OOO_CHANNEL'))
