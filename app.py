""" Slacky bot for slack """
import os

from dotenv import load_dotenv
from flask import Flask
from flask import request
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from slack_sdk import WebClient

from bot_handlers.pto_register import PTORegister
from handlers.database.google_sheet import GoogleSheetDB

if not os.getenv('ENV'):
    load_dotenv()

app = Flask(__name__)

client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))
bolt_app = App(token=os.environ.get("SLACK_BOT_TOKEN"),
               signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
               url_verification_enabled=True
               )

google_sheet_db = GoogleSheetDB(
    service_account_file_content=os.getenv('GOOGLE_SERVICE_BASE64_FILE_CONTENT'), is_encode_base_64=True)
PTORegister(bolt_app, client, google_sheet_db,
            leave_register_sheet=os.getenv('LEAVE_REGISTER_SHEET'),
            approval_channel=os.getenv('MANAGER_LEAVE_APPROVAL_CHANNEL'))
handler = SlackRequestHandler(bolt_app)


@app.route("/slack-bot/events", methods=["POST"])
def slack_events():
    """ Declaring the route where slack will post a request and dispatch method of App """
    return handler.handle(request)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
