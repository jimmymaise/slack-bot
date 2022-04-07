## Introduction

BIP Bot is a slack bot providing a better way to implement the Bimodal Internal Process

At the very first MVP, BIP Bot will help us to schedule the PTO time Read
the [BIP - leave management & attendance management](https://docs.google.com/document/d/1ruRofzWX7pkLEdNZ9T7N71tEV6AL0zmx5DcLW2OSNb8/edit)
for understanding requirements

## How to create an internal bot

1. Visit: https://api.slack.com/

2. Click "Create an app", select from Scratch

3. Fill in the request information
    1. Make sure we are saving changes as we follow these next steps

4. In 'Basic Information' under 'Settings' we can scroll all the way down to change the bot icon/name/description

5. Go to 'OAuth & Permissions' under 'Features'. Then scoll down to the 'Scopes' section and add an OAuth scope for:

    - channels:history
    - channels:manage
    - channels:read
    - chat:write
    - chat:write.public
    - commands
    - groups:history
    - groups:read
    - im:read
    - im:write
    - mpim:read
    - reactions:read
    - team:read
    - users:read
    - usergroups:read

6. In the same section, we will find a 'Bot User OAuth Access Token'. Copy and use it as `SLACK_BOT_TOKEN` for
   environment variable

7. Go to 'Basic Information' under 'Settings', click show next to the 'Signing Secret'. Copy and use it
   as `SLACK_SIGNING_SECRET` for environment variable

8. In the same section, click 'Install our app' into the workspace. Allow the requested access.

Assume that we have deployed the bot to the Lambda (Check Deployment stage below) and have
the `permanent address`: https://xyz123.execute-api.us-west-1.amazonaws.com/slack-bot-bip

9. Then go to 'Event Subscriptions' under 'Features'. In the 'Request URL' field type the above address. We should see a
   green 'Verified' checkmark above the text-field

10. Check the 'Subscribe to bot events' section below, add some events:
    1. message.channels
    2. message.groups
    3. app_home_opened
    4. team_join

11. Go to 'Interactivity & Shortcuts' under 'Features'. In the 'Request URL' field type the above address

12. Go to 'Slash Commands' under 'Features'.Fill in the information:
    1. In the 'Command' field type in: "/vacation
    2. Continue to the above link for Requests URL
    3. Repeat 1&2 with command "/ooo-today"

13. Go to 'App Home' under 'Features'. Enable tabs in Show Tabs
    1. Home Tab
    2. Message Tab

14. Add the bot to the manager approval channel for posting the message

## Deployment

### Preparation

Enter folder terraform and check variables in variables.tf. Create a secret.tfvars for these variables

`SLACK_SIGNING_SECRET`: Slack signs its requests using this secret that's unique to our app. It has format like
a1bc2345.....

`SLACK_BOT_TOKEN`: The OAuth token we use to call the Slack API has access to the data on the workspace where it is
installed. It has format like xoxb-123....

`GOOGLE_SERVICE_BASE64_FILE_CONTENT`: The Base64 encoded of the content of Google Service Account Key File (Json File).
As this account needs to access Google sheet, so we must enable the Google Sheets API
Read [this instruction](https://support.google.com/a/answer/7378726?hl=en) to know how to create service account and
enable Google Sheets API. After having the service account, go to key tab and click Add key. A new key file will be
downloaded. Open this file and encode its content as base64

`LEAVE_REGISTER_SHEET`: The url of the Google sheet that the bot uses to put the leave record. We also need to invite
the Service account to access this file (Example jimmy-301@elated-chariot-341105.iam.gserviceaccount.com)

`MANAGER_LEAVE_APPROVAL_CHANNEL`: The manager's channel to push the leave of request for approval. We should also invite
the bot to this channel. For example #my_testing_channel (Should have #)

`REGION`: The AWS region

`OOO_CHANNEL`: The channel to get ooo notification

### Deploy steps

1. Install Docker if don't have

2. docker pull lambci/lambda:build-python3.8

3. Setup backend bucket

    1. Add below environment variable to the deployment machine. Replace us-west-2 and leave-management-bimodal depend
       on environment you are working for (using us-west-1 and dev-leave-management-bimodal for dev env)
        1. export REGION="us-west-2"
        2. export S3_BACKEND_BUCKET="leave-management-bimodal"
    2. aws s3api create-bucket --bucket "${S3_BACKEND_BUCKET}" --region "${REGION}" --create-bucket-configuration
       LocationConstraint="${REGION}"
    3. terraform init -backend-config="bucket="${S3_BACKEND_BUCKET}"" -backend-config="region="${REGION}""

4. terraform apply --var-file=secret.tfvars

5. Get the permanent URL and use it to update slack bot (step 9, 11, 12)

## How to run the bot locally for debuging

1. Run file local_run.py
2. Using application like ngrok to map a localhost address to an internet address
3. Using this internet address to bot configuration (http://abc-..-..-xyz.ngrok.io)

## How to use the bot

Currently, the bot just support two commands `/vacation` and `/ooo-today`. Let's play with it.

## How to setup Github Action

Go to Repo Settings->Secrets->Action and add below secrets (Using repo secret not organization secret)

AWS_ACCESS_KEY_ID

AWS_REGION

AWS_SECRET_ACCESS_KEY

TF_VAR_BUILD_IN_DOCKER (value should be false as Github Action runner doesn't have Docker)

TF_VAR_GOOGLE_SERVICE_BASE64_FILE_CONTENT

TF_VAR_LEAVE_REGISTER_SHEET

TF_VAR_MANAGER_LEAVE_APPROVAL_CHANNEL

TF_VAR_OOO_CHANNEL

TF_VAR_S3_BACKEND_BUCKET

TF_VAR_SLACK_BOT_TOKEN

TF_VAR_SLACK_SIGNING_SECRET

TF_VAR_TEAM_SHEET TF_VAR_TEAM_MEMBER_SHEET

TF_VAR_LEAVE_TYPE_SHEET

TF_VAR_MUST_READ_SHEET

With dev env, we will add the prefix DEV_, Example: TF_VAR_LEAVE_TYPE_SHEET becomes DEV_TF_VAR_LEAVE_TYPE_SHEET

## How to create CI user

1. Cd to folder tf_ci_account
2. Add below environment variable to the deployment machine. Replace us-west-2 and leave-management-bimodal depend on
   environment you are working for.
    1. export REGION="us-west-2"
    2. export S3_BACKEND_BUCKET="leave-management-bimodal"
3. terraform init -backend-config="bucket="
   ${S3_BACKEND_BUCKET}"" -backend-config="region="${REGION}""
4. terraform apply
5. Run below command to get the secret key (You must have jq)
    1. terraform state pull | jq '.resources[] | select(.type == "aws_iam_access_key") | .instances[0]
       .attributes.secret'
6. copy aws access key, aws secret key and use them for Github actions

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what we would like to change.

Please make sure to update tests as appropriate.

## License

[MIT](https://choosealicense.com/licenses/mit/)
