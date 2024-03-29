provider "aws" {
  region = var.REGION
}

terraform {
  backend "s3" {
    key = "bimodal_slack_bot"
  }
}

module "lambda_function" {
  source                = "registry.terraform.io/terraform-aws-modules/lambda/aws"
  publish               = true
  timeout               = 900
  environment_variables = {
    SLACK_SIGNING_SECRET               = var.SLACK_SIGNING_SECRET
    SLACK_BOT_TOKEN                    = var.SLACK_BOT_TOKEN
    GOOGLE_SERVICE_BASE64_FILE_CONTENT = var.GOOGLE_SERVICE_BASE64_FILE_CONTENT
    DB_SPREADSHEET_ID = var.DB_SPREADSHEET_ID
  }
  function_name         = "slack-bot-bip"
  description           = "Slack bot bip for lambda"
  handler               = "lambda_handler.handler"
  build_in_docker       = var.BUILD_IN_DOCKER
  docker_image          = "lambci/lambda:build-python3.8"
  runtime               = "python3.8"
  source_path           = [
    {
      path             = "..",
      pip_requirements = true,
      patterns         = [
        "!terraform/.*",
        "!tf_ci_account/.*",
        "!.github/.*",
        "!.env",
        "!.idea/.*",
        "!.git/.*",
        "!node_modules/.*",
        "application/.*",
        "lambda_handler.py",
        "!./../__pycache__/.*"
      ]

    }
  ]
  allowed_triggers      = {
    APIGatewayAny = {
      service    = "apigateway"
      source_arn = "${module.api_gateway.apigatewayv2_api_execution_arn}/*/*/${module.lambda_function.lambda_function_name}"
      stage      = ""
    }
  }
  tags                  = {
    Name = "slack-bot-bip"
  }
}

module "api_gateway" {
  source                 = "registry.terraform.io/terraform-aws-modules/apigateway-v2/aws"
  create_api_domain_name = false
  name                   = "dev-http"
  description            = "My awesome HTTP API Gateway"
  protocol_type          = "HTTP"

  cors_configuration = {
    allow_headers = [
      "content-type", "x-amz-date", "authorization", "x-api-key", "x-amz-security-token", "x-amz-user-agent"
    ]
    allow_methods = ["*"]
    allow_origins = ["*"]
  }

  # Custom domain
  domain_name                 = null
  domain_name_certificate_arn = null

  # Access logs
  default_stage_access_log_format = "$context.identity.sourceIp - - [$context.requestTime] \"$context.httpMethod $context.routeKey $context.protocol\" $context.status $context.responseLength $context.requestId $context.integrationErrorMessage"

  # Routes and integrations
  integrations = {
    "ANY /${module.lambda_function.lambda_function_name}" = {
      lambda_arn             = module.lambda_function.lambda_function_invoke_arn
      payload_format_version = "2.0"
      timeout_milliseconds   = 12000
    }

    "$default" = {
      lambda_arn = module.lambda_function.lambda_function_invoke_arn
    }
  }

  tags = {
    Name = "slack-bot-http-apigateway"
  }
}

resource "aws_iam_policy" "lambda_invoke_itself" {
  name        = "lambda-invoke-itself"
  description = "lambda_invoke_itself"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "VisualEditor0",
      "Effect": "Allow",
      "Action": [
        "lambda:InvokeFunction",
        "lambda:GetFunction"
      ],
      "Resource": "*"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "add_permission_for_lambda_invoke_itself" {
  role       = module.lambda_function.lambda_role_name
  policy_arn = aws_iam_policy.lambda_invoke_itself.arn
}

//Schedule

module "trigger_must_read" {
  source                      = "./modules/cloud_watch_event_trigger_lambda_schedule"
  schedule_name               = "trigger_must_read"
  schedule_desc               = "trigger_must_read"
  schedule_expression         = "cron(0 16 ? * MON-FRI *)"
  schedule_lambda_target_arn  = module.lambda_function.lambda_function_arn
  schedule_lambda_target_name = module.lambda_function.lambda_function_name
  trigger_input               = { "lambda_trigger_event" : "SCHEDULER_MUST_READ" }
}

module "trigger_today_ooo" {
  source                      = "./modules/cloud_watch_event_trigger_lambda_schedule"
  schedule_name               = "trigger_today_ooo"
  schedule_desc               = "trigger_today_ooo"
  schedule_expression         = "cron(0 16 ? * MON-FRI *)"
  schedule_lambda_target_arn  = module.lambda_function.lambda_function_arn
  schedule_lambda_target_name = module.lambda_function.lambda_function_name
  trigger_input               = { "lambda_trigger_event" : "SCHEDULER_OOO_TODAY" }
}

module "trigger_lambda_warm_up" {
  source                      = "./modules/cloud_watch_event_trigger_lambda_schedule"
  schedule_name               = "trigger_lambda_warm_up"
  schedule_desc               = "trigger_lambda_warm_up"
  schedule_expression         = "rate(5 minutes)"
  schedule_lambda_target_arn  = module.lambda_function.lambda_function_arn
  schedule_lambda_target_name = module.lambda_function.lambda_function_name
  trigger_input               = { "lambda_trigger_event" : "SCHEDULER_WARM_UP_LAMBDA" }
}


output "lambda_url" {
  description = "lambda_url"
  value       = "${module.api_gateway.apigatewayv2_api_api_endpoint}/${module.lambda_function.lambda_function_name}"
}


output "bot-lambda-address" {
  description = "apigatewayv2_api_execution_arn"
  value       = module.api_gateway.apigatewayv2_api_execution_arn
}
