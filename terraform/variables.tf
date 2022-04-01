variable "SLACK_SIGNING_SECRET" {
  type = string
}
variable "SLACK_BOT_TOKEN" {
  type = string
}
variable "GOOGLE_SERVICE_BASE64_FILE_CONTENT" {
  type = string
}
variable "TEAM_SHEET" {
  type    = string
}
variable "TEAM_MEMBER_SHEET" {
  type    = string
}
variable "LEAVE_REGISTER_SHEET" {
  type    = string
}
variable "LEAVE_TYPE_SHEET" {
  type    = string
}
variable "MANAGER_LEAVE_APPROVAL_CHANNEL" {
  default = "#bimodal-qpto-internal-project"
  type    = string
}

variable "REGION" {
  default = "us-west-2"
  type    = string
}

variable "OOO_CHANNEL" {
  default = "#bimodal-qpto-internal-project"
  type    = string
}
variable "BUILD_IN_DOCKER" {
  default = true
}
