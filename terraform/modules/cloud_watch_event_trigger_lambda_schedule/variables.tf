variable "schedule_name" {
  type = string
}
variable "schedule_desc" {
  type = string
}

variable "schedule_expression" {
  type = string
}

variable "schedule_lambda_target_arn" {
  type = string
}
variable "schedule_lambda_target_name" {
  type = string
}

variable "trigger_input" {
  type = map
}



