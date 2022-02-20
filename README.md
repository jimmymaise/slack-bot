# Introduction

BIP Bot is a slack bot providing a better way to implement the Bimodal Internal Process

At the very first MVP, BIP Bot will help us to schedule the PTO time
Read the [BIP - leave management & attendance management](https://docs.google.com/document/d/1ruRofzWX7pkLEdNZ9T7N71tEV6AL0zmx5DcLW2OSNb8/edit) for understanding requirements
## Installation
Deploy this one to Lambda
## Usage
### Setup environment variables

`SLACK_SIGNING_SECRET`: Slack signs its requests using this secret that's unique to our app. It has format like a1bc2345.....

`SLACK_BOT_TOKEN`: The OAuth token we use to call the Slack API has access to the data on the workspace where it is installed. It has format like xoxb-123....

`GOOGLE_SERVICE_BASE64_FILE_CONTENT`: The Base64 encoded of the content of Google Service Account File (Json File). Read [this instruction](https://support.google.com/a/answer/7378726?hl=en) to know how to create service account

`LEAVE_REGISTER_SHEET`: The url of the Google sheet that the bot uses to put the leave record. We also need to invite the Service account to access this file (Example jimmy-301@elated-chariot-341105.iam.gserviceaccount.com)

`MANAGER_LEAVE_APPROVAL_CHANNEL`: The manager's channel to push the leave of request for approval. We should also invite the bot to this channel

### How to create an internal bot
1. Visit: https://api.slack.com/

2. Click "Start Building"

3. Fill in the request information 
   1. Make sure we are saving changes as we follow these next steps
   
4. In 'Basic Information' under 'Settings' we can scroll all the way down to change the bot icon/name/description

5. Go to 'OAuth & Permissions' under 'Features'. Then scoll down to the 'Scopes' section and add an OAuth scope for:

   1. channels:history 
   2. channels:manage
   3. channels:read
   4. chat:write 
   5. commands
   6. groups:history
   7. groups:read
   8. im:read
   9. mpim:read
   10. team:read
   11. users:read

6. In the same section, we will find a 'Bot User OAuth Access Token'. Copy and use it as `SLACK_BOT_TOKEN` for environment variable

7. Go to 'Basic Information' under 'Settings', click show next to the 'Signing Secret'. Copy and use it as `SLACK_SIGNING_SECRET` for environment variable

8. In the same section, click 'Install our app' into the workspace. Allow the requested access.

Assume that we have deployed the bot to the server and have the `fixed address`: https://bimodal-bot-example.com/slack-bot/events

9. Then go to 'Event Subscriptions' under 'Features'. In the 'Request URL' field type https://bimodal-bot-example.com/slack-bot/events. We should see a green 'Verified' checkmark above the text-field 

10. Check the 'Subscribe to bot events' section below, add some events:
    1. message.channels
    2. message.groups
   
11. Go to 'Interactivity & Shortcuts' under 'Features'. In the 'Request URL' field type the above address

12. Go to 'Slash Commands' under 'Features'.Fill in the information:
    1. In the 'Command' field type in: "/vacation
    2. Continue to the above link for Requests URL 

13. Add the bot to the manager approval channel for posting the message

## How to use the bot
Currently, the bot just support only one command `/vacation`. Let's play with it.


## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what we would like to change.

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)

