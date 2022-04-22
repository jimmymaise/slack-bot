variable "SLACK_SIGNING_SECRET" {
  type = string
}
variable "SLACK_BOT_TOKEN" {
  type = string
}
variable "GOOGLE_SERVICE_BASE64_FILE_CONTENT" {
  type = string
}

variable "REGION" {
  default = "us-west-2"
  type    = string
}

variable "BUILD_IN_DOCKER" {
  default = true
}

variable "DB_SPREADSHEET_ID" {
  type    = string
}
