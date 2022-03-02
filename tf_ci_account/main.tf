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
                "s3:ListBucket",
                "s3:GetObject",
                "ec2:DescribeAccountAttributes",
                "events:DescribeRule",
                "logs:DescribeLogGroups",
                "events:ListTagsForResource",
                "logs:ListTagsLogGroup",
                "apigateway:GET",
                "iam:GetRole",
                "iam:GetPolicy",
                "iam:GetPolicyVersion",
                "iam:ListRolePolicies",
                "iam:ListAttachedRolePolicies",
                "lambda:GetFunction",
                "lambda:ListVersionsByFunction",
                "lambda:GetFunctionCodeSigningConfig",
                "lambda:GetPolicy",
                "events:ListTargetsByRule",
                "events:RemoveTargets",
                "lambda:RemovePermission",
                "events:DeleteRule",
                "apigateway:DELETE",
                "iam:DetachRolePolicy",
                "iam:ListPolicyVersions",
                "iam:DeletePolicy",
                "lambda:DeleteFunction",
                "iam:ListInstanceProfilesForRole",
                "logs:DeleteLogGroup",
                "iam:DeleteRole",
                "s3:PutObject",
                "logs:CreateLogGroup",
                "events:PutRule",
                "iam:PassRole",
                "iam:CreatePolicy",
                "iam:CreateRole",
                "iam:TagPolicy",
                "iam:TagRole",
                "apigateway:POST",
                "apigateway:TagResource",
                "iam:AttachRolePolicy",
                "lambda:CreateFunction",
                "lambda:AddPermission",
                "events:PutTargets"
            ],
            "Resource": "*"
        }
    ]
}
EOF
}

data "template_file" "secret" {
  template = aws_iam_access_key.slack_bot_key.secret
}
output "aws_access_key" {
  value     = aws_iam_access_key.slack_bot_key.id
}
output "aws_access_secret" {
  value     = data.template_file.secret.rendered
}
