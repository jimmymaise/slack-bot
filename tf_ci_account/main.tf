terraform {
  backend "s3" {
    key = "ci_account_bimodal_slack_bot"
  }
}
resource "aws_iam_access_key" "slack_bot_key" {
  user = aws_iam_user.slackbot.name
}

resource "aws_iam_user" "slackbot" {
  name = "slack-bot-tf-deploy"
  path = "/terraform/"
}

resource "aws_iam_user_policy" "deploy_slack_bot_lambda" {
  name = "deploy_slack_bot_lambda"
  user = aws_iam_user.slackbot.name

  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:*",
                "logs:*",
                "iam:*",
                "apigateway:*",
                "lambda:*",
                "events:*"
            ],
            "Resource": "*"
        }
    ]
}
EOF
}


output "aws_access_key" {
  value = aws_iam_access_key.slack_bot_key.id
}
output "aws_access_secret" {
  value = "Run command in Readme doc to get the secret case. Remember install jq before doing so"
}

