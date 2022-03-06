resource "aws_cloudwatch_event_rule" "this" {
  name                = var.schedule_name
  description         = var.schedule_desc
  schedule_expression = var.schedule_expression

}

resource "aws_cloudwatch_event_target" "this" {
  rule  = aws_cloudwatch_event_rule.this.name
  arn   = var.schedule_lambda_target_arn
  input = jsonencode(var.trigger_input)
}

resource "aws_lambda_permission" "allow_cloudwatch_to_call_lambda_function" {
  statement_id  = aws_cloudwatch_event_rule.this.name
  action        = "lambda:InvokeFunction"
  function_name = var.schedule_lambda_target_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.this.arn
}
