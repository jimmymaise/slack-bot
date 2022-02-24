variable "SLACK_SIGNING_SECRET" {
  type = string
}
variable "SLACK_BOT_TOKEN" {
  type = string
}
variable "GOOGLE_SERVICE_BASE64_FILE_CONTENT" {
  type = string
}
variable "LEAVE_REGISTER_SHEET" {
  default = "https://docs.google.com/spreadsheets/d/1QUU0J_LaggqQQHmCFnQfzFXngl9ECqfE96qwwqT2ADM/edit#gid=1723079437"
  type    = string
}
variable "MANAGER_LEAVE_APPROVAL_CHANNEL" {
  default = "#manager_leave_approval"
  type    = string
}

variable "region" {
  default = "us-west-2"
  type    = string
}