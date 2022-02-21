from slack_bolt import App, BoltContext
from slack_sdk import WebClient

from application.handlers.bot.pto_register import PTORegister


class HomeTab:
    def __init__(self, app: App, client: WebClient):
        self.app = app
        self.client = client
        app.event("app_home_opened")(ack=self.respond_to_slack_within_3_seconds, lazy=[self.app_home_opened_lazy])
        app.block_action({"block_id": "home_tab", "action_id": "book_vacation"})(
            ack=self.respond_to_slack_within_3_seconds, lazy=[PTORegister.request_leave_command])

    @staticmethod
    def respond_to_slack_within_3_seconds(ack):
        ack()

    def app_home_opened_lazy(self, event, context: BoltContext, client: WebClient):
        if event["tab"] == "home":
            # and event.get("view") is None
            client.views_publish(user_id=context.user_id, view=self.home_view())

    @staticmethod
    def home_view() -> dict:
        print('Update home view')
        blocks = [
            {
                "type": "section",

                "text": {
                    "type": "mrkdwn",
                    "text": "BIP Bot is a slack bot providing a better way to implement the Bimodal Internal Process "
                            "At the very first MVP, BIP Bot will help us to schedule the PTO time "
                            "Read the <https://docs.google.com/document/d/1ruRofzWX7pkLEdNZ9T7N71tEV6AL0zmx5DcLW2OSNb8/edit|*[BIP - leave management & attendance management]> for understanding requirements"
                }
            },
            {
                "block_id": "home_tab",
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "action_id": "book_vacation",

                        "text": {
                            "type": "plain_text",
                            "text": "Book vacation",
                            "emoji": True
                        }
                    }
                ]
            }
        ]

        return {"type": "home", "blocks": blocks}
