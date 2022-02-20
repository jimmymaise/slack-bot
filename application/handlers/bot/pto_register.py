import datetime
import uuid

from slack_bolt import App
from slack_sdk import WebClient

from application.handlers.database.google_sheet import GoogleSheetDB


class PTORegister:
    def __init__(self, app: App, client: WebClient, google_sheet_db: GoogleSheetDB,
                 leave_register_sheet, approval_channel: str):
        self.app = app
        self.client = client
        self.google_sheet_db = google_sheet_db
        self.leave_register_sheet = leave_register_sheet
        self.approval_channel = approval_channel
        app.command('/vacation')(self.request_leave_command)
        app.view('view_1')(ack=self.respond_to_slack_within_3_seconds, lazy=[self.handle_submission])
        app.block_action({"block_id": "approve_deny_vacation", "action_id": "approve"})(
            ack=self.respond_to_slack_within_3_seconds, lazy=[self.approve_pto])
        app.block_action({"block_id": "approve_deny_vacation", "action_id": "deny"})(
            ack=self.respond_to_slack_within_3_seconds,
            lazy=[self.deny_pto])

    @staticmethod
    def respond_to_slack_within_3_seconds(ack):
        ack()

    def request_leave_command(self, body, ack):
        self.client.views_open(
            trigger_id=body.get('trigger_id'),
            view={
                "type": "modal",
                "callback_id": "view_1",

                "title": {"type": "plain_text", "text": "Request a leave"},
                "close": {"type": "plain_text", "text": "Close"},
                "submit": {"type": "plain_text", "text": "Submit"},
                "blocks": [

                    {
                        "type": "input",
                        "block_id": "leave_type",

                        "label": {
                            "type": "plain_text",
                            "text": "Leave Type"
                        },
                        "element": {
                            "action_id": "leave_type",
                            "type": "static_select",
                            "placeholder": {
                                "type": "plain_text",
                                "text": "Select leave type"
                            },
                            "initial_option":
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": ":palm_tree:PTO",
                                        "emoji": True

                                    },
                                    "value": "PTO"
                                },
                            "options": [
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": ":palm_tree:PTO",
                                        "emoji": True

                                    },
                                    "value": "PTO"
                                },
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": ":palm_tree:Quarter PTO",
                                        "emoji": True

                                    },
                                    "value": "Quarter PTO"
                                },
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": ":money_with_wings:UTO",
                                        "emoji": True

                                    },
                                    "value": "UTO"
                                },
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": ":thermometer:Sick",
                                        "emoji": True

                                    },
                                    "value": "Sick"
                                }
                            ]
                        }
                    },
                    {
                        "type": "input",
                        "optional": False,

                        "block_id": "vacation_start_date",
                        "label": {
                            "type": "plain_text",
                            "text": "Start date:"
                        },
                        "element": {
                            "type": "datepicker",
                            "action_id": "vacation_start_date_picker",
                            "placeholder": {
                                "type": "plain_text",
                                "text": "Select a date"
                            }
                        }
                    },
                    {
                        "type": "input",
                        "optional": False,
                        "block_id": "vacation_end_date",
                        "label": {
                            "type": "plain_text",
                            "text": "End date:"
                        },
                        "element": {
                            "type": "datepicker",
                            "action_id": "vacation_end_date_picker",
                            "placeholder": {
                                "type": "plain_text",
                                "text": "Select a date"
                            }
                        }
                    },
                    {
                        "type": "input",
                        "block_id": "reason_of_leave",
                        "label": {
                            "type": "plain_text",
                            "text": "Details (optional)",
                        },
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "reason_for_leave",
                            "multiline": True,
                            "placeholder": {
                                "type": "plain_text",
                                "text": "Specific why you're taking the time off."
                            }
                        }
                    },
                ],
            }
        )

        ack()

    # Update the view on submission
    def handle_submission(self, body, logger):
        time_now = datetime.datetime.now()
        workspace_domain = f"https://{self.client.team_info().get('team').get('domain')}.slack.com/team/"
        user = body.get("user")
        user_id = user.get("id")
        user_info = self.client.users_info(user=user_id)
        user_name = user_info.get("user").get("real_name")
        user_profile_url = workspace_domain + user_id

        values = body.get("view").get("state").get("values")
        reason_of_leave = values.get("reason_of_leave").get("reason_for_leave").get("value")
        leave_type = values.get("leave_type").get("leave_type").get("selected_option").get('value')

        start_date_str = values.get("vacation_start_date").get("vacation_start_date_picker").get("selected_date")
        end_date_str = values.get("vacation_end_date").get("vacation_end_date_picker").get("selected_date")
        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d')
        leave_id = uuid.uuid4()

        self.client.chat_postMessage(
            channel=self.approval_channel,
            text=f"You have a new request:\n*<{user_profile_url}|{user_name} - New vacation request>*",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"You have a new request:\n*<{user_profile_url}|{user_name} - New vacation request>*"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Reason:*\n{reason_of_leave}"
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Leave Type:*\n{leave_type}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Leave Id:*\n{leave_id}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "fields": [
                        {

                            "type": "mrkdwn",
                            "text": f"*Start Date:*\n{start_date.strftime('%A, %B, %d, %Y')}"

                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*End Date:*\n{end_date.strftime('%A, %B, %d, %Y')}"

                        }
                    ]
                },
                {
                    "type": "actions",
                    "block_id": "approve_deny_vacation",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "emoji": True,
                                "text": "Approve"
                            },
                            "action_id": "approve",
                            "style": "primary",
                            "value": "approve_vacation_request"
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "emoji": True,
                                "text": "Deny"
                            },
                            "action_id": "deny",
                            "style": "danger",
                            "value": "deny_vacation_request"
                        }
                    ]
                }
            ])
        logger.info(body)
        self.client.chat_postMessage(channel=user_id,
                                     text=f"You have sent a new vacation request. "
                                          f"Please wait to manager approve",
                                     blocks=[{
                                         "type": "section",
                                         "text": {
                                             "type": "mrkdwn",
                                             "text": f"You have sent a new vacation request. "
                                                     f"Please wait to manager approve"
                                         }
                                     },

                                         {
                                             "type": "section",
                                             "fields": [
                                                 {
                                                     "type": "mrkdwn",
                                                     "text": f"*Leave Type:*\n{leave_type}"
                                                 },
                                                 {
                                                     "type": "mrkdwn",
                                                     "text": f"*Leave Id:*\n{leave_id}"
                                                 }
                                             ]
                                         },
                                         {
                                             "type": "section",
                                             "fields": [
                                                 {
                                                     "type": "mrkdwn",
                                                     "text": f"*Start Date:*\n{start_date.strftime('%A, %B, %d, %Y')}",
                                                 },
                                                 {
                                                     "type": "mrkdwn",
                                                     "text": f"*End Date:*\n{end_date.strftime('%A, %B, %d, %Y')}",
                                                 }
                                             ]
                                         },
                                         {
                                             "type": "section",
                                             "fields": [
                                                 {
                                                     "type": "mrkdwn",
                                                     "text": f"*Reason:*\n{reason_of_leave}"
                                                 }
                                             ]
                                         },

                                     ])

        query = f"""INSERT INTO 
        "{self.leave_register_sheet}" ("Leave Id","Username","Start date","End date",
        "Leave type","Reason","Created time","Status")
        VALUES ("{leave_id}","{user_name}","{start_date_str}","{end_date_str}","{leave_type}",
        "{reason_of_leave}","{time_now}","Wait for Approval")
                     """
        print(query)
        self.google_sheet_db.cursor.execute(query)

    def approve_pto(self, ack, body, logger):
        self._process_pto_actions(body, ack)

    def deny_pto(self, ack, body, logger):
        self._process_pto_actions(body, ack)

    def _process_pto_actions(self, body, ack):
        container = body.get("container")
        message_ts = container.get("message_ts")
        channel_id = container.get("channel_id")
        decision = body.get("actions")[0].get("text").get("text")
        leave_id = body['message']['blocks'][2]['fields'][1]['text'].split(':*\n')[1].strip()
        start_date = body['message']['blocks'][3]['fields'][0]['text'].split(':*')[1].strip()
        end_date = body['message']['blocks'][3]['fields'][1]['text'].split(':*\n')[1].strip()
        # Manager info
        manager_id = body.get('user').get('id')
        manager_info = self.client.users_info(user=manager_id)

        manager_name = manager_info.get("user").get("real_name")
        # User info
        temp = body.get('message').get('blocks')[0].get('text').get('text')
        user_id = temp[temp.index('/U') + 1: temp.index('|')]
        user_info = self.client.users_info(user=user_id)
        user_name = user_info.get("user").get("real_name")

        # Delete responded message
        self.client.chat_delete(channel=channel_id, ts=message_ts)
        if decision == "Approve":
            # leave_detail_query = f"""INSERT
            #        INTO "{self.leave_register_sheet}" (Staff, "Leave type","Date","Approved by")
            #        VALUES ("Duyet Mai","PTO","01/04/2022","Kame")
            #        """

            self.client.chat_postMessage(channel="#manager_leave_approval",
                                         text=f":tada:Leave Request for {user_name} (From {start_date} To {end_date}) "
                                              f"has been approved by {manager_name}. Leave Id: {leave_id}")
            self.client.chat_postMessage(channel=user_id,
                                         text=f":tada:Your leave request (From {start_date} to {end_date}) "
                                              f"has been approved by {manager_name}:smiley: . Leave Id: {leave_id}")
        else:
            self.client.chat_postMessage(channel="#manager_leave_approval",
                                         text=f":x:Leave Request for {user_name} (From {start_date} To {end_date}) "
                                              f"has been denied by {manager_name} . Leave Id: {leave_id}")
            self.client.chat_postMessage(channel=user_id,
                                         text=f":x:Your leave request (From {start_date} To {end_date}) has been denied by {manager_name} :cry: . Leave Id: {leave_id}")

        update_approve = f"""UPDATE "{self.leave_register_sheet}"
             SET "Approver" = "{manager_name}" , "Status" ="{decision}"
              where "Leave Id" = "{leave_id}"
             """

        self.google_sheet_db.cursor.execute(update_approve)

        ack()
