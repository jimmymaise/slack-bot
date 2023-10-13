# Slack Bot README

## Overview

This document outlines the steps for setting up, deploying, and managing an internal Slack bot. The bot is designed to be hosted on AWS Lambda and works with Google Sheets via a service account. Below you'll find guidelines for local debugging, deploying via Terraform, and incorporating CI/CD through GitHub Actions.

## Setting Up the Slack Bot

### Initial Configuration

1. Navigate to [Slack API Portal](https://api.slack.com/)
2. Click on "Create an app" and choose "From Scratch."
3. Complete the required fields.
    - Remember to save your changes regularly.

### Personalize Your Bot

1. Under 'Settings' → 'Basic Information', you can customize the bot's icon, name, and description.

### Setting Permissions

1. Visit 'Features' → 'OAuth & Permissions'.
2. In the 'Scopes' section, add the following OAuth scopes:
    - channels:history
    - channels:manage
    - channels:read
    - chat:write
    - and others (see original README for complete list)

3. Retrieve your 'Bot User OAuth Access Token' and set it as an environment variable `SLACK_BOT_TOKEN`.
4. Obtain the 'Signing Secret' from 'Settings' → 'Basic Information', and set it as `SLACK_SIGNING_SECRET`.

### Installation & Event Configuration

1. Install the bot into your workspace and grant the necessary permissions.
2. Go to 'Features' → 'Event Subscriptions' and set the Request URL to your Lambda URL.
3. Subscribe the bot to events like `message.channels`, `message.groups`, etc.

### Interactivity & Slash Commands

1. In 'Features' → 'Interactivity & Shortcuts', set the Request URL to your Lambda URL.
2. Under 'Slash Commands', define commands such as `/vacation` and `/ooo-today`.

### App Home Customization

1. In 'Features' → 'App Home', enable the Home and Message Tabs.
2. Add the bot to the manager approval channel for posting messages.

## Deployment with Terraform

### Prerequisites

- Set your environment variables as outlined in `variables.tf`.
- Have Docker installed.

### Steps

1. Pull the Docker image: `docker pull lambci/lambda:build-python3.8`.
2. Initialize your Terraform backend and apply the configuration.

## Local Debugging

- Run `local_run.py`.
- Use tools like ngrok for tunneling.

## Bot Commands

The bot currently supports `/vacation` and `/ooo-today`.

## GitHub Actions Setup

Add the specified secrets under 'Repo Settings' → 'Secrets' → 'Action'.

## Create CI User

Follow the steps in the original README to create a CI user for deployments.

## Contributing

Feel free to open pull requests or issues for significant changes. Remember to update the tests accordingly.

## License

Licensed under the [MIT License](https://choosealicense.com/licenses/mit/).
