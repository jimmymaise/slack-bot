from __future__ import annotations

import os

from slack_bolt.adapter.aws_lambda import SlackRequestHandler
from slack_bolt.app import App
from slack_sdk import WebClient

from application.utils.constant import Constant
from slack_listener import SlackListener

client = WebClient(token=os.environ.get('SLACK_BOT_TOKEN'))
bolt_app = App(
    token=os.environ.get('SLACK_BOT_TOKEN'),
    signing_secret=os.environ.get('SLACK_SIGNING_SECRET'),
    url_verification_enabled=True,
    request_verification_enabled=False,
    process_before_response=True,
)
slack_listener = SlackListener(bolt_app, client)


def handler(event, context):
    schedule_event = event.get('lambda_trigger_event')
    if schedule_event:
        print(schedule_event)
        schedule_process(schedule_event)
    slack_handler = SlackRequestHandler(app=bolt_app)
    return slack_handler.handle(event, context)


def schedule_process(schedule_event):
    if schedule_event == Constant.SCHEDULER_OOO_TODAY:
        slack_listener.leave_lookup.today_ooo_schedule(os.getenv('OOO_CHANNEL'))
