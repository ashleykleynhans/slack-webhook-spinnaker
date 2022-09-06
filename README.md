# Slack Compatible API Webhook Receiver to Send Notifications for Spinnaker

## Supported Notifications

The following platforms are currently supported:

* Discord
* Slack
* Telegram
* Webex

## Background

[Spinnaker](https://spinnaker.io/) supports sending various types of notifications
to various different kinds of applications through the [Echo](
https://github.com/spinnaker/echo) microservice.

However,  [Echo](https://github.com/spinnaker/echo) does not currently support sending
notifications to various different platforms such as Discord, Telegram or Webex.

[Echo](https://github.com/spinnaker/echo) supports a REST webhook receiver, but every
single event, including Igor health checks get sent to the webhook, so it becomes
rather spammy.

[Echo](https://github.com/spinnaker/echo) allows you to override the [Slack](
https://docs.armory.io/armory-enterprise/installation/armory-operator/op-manifest-reference/notification/#slack-parameters)
`baseUrl` and set `forceUseIncomingWebhook` to `true` and then you can use a Slack
compatible webhook receiver to handle your notifications, which is what this webhook
receiver does, provided that you have configured [Echo](https://github.com/spinnaker/echo)
correctly.

## Prerequisites

### General prerequisites

1. Install [ngrok](https://ngrok.com/).
```bash
brew install ngrok
```
2. Ensure your System Python3 version is 3.9, but greater than 3.9.1.
```bash
python3 -V
```
3. If your System Python is not 3.9:
```bash
brew install python@3.9
brew link python@3.9
```
4. If your System Python is 3.9 but not greater than 3.9.1:
```bash
brew update
brew upgrade python@3.9
```

### Telegram prerequisites

1. [Create a new Telegram Bot](https://core.telegram.org/bots#creating-a-new-bot)
and take note of the Bot Token.
2. Create your Telegram channels where you want to receive your Spinnaker
notifications and add the bot into them as an Admin user. These channels can
either be public or private, if they are public, the CHAT ID will be in the
format of `@my_channel` and if they are private, the CHAT ID will be in the
format of `-1000000000000`.
3. If you created private channels, you need to obtain the CHAT IDs for the
channels by running the following curl command:
```
curl https://api.telegram.org/<TELEGRAM_BOT_TOKEN>/getUpdates
```
This will output a JSON response, where you need to look for the `my_chat_member` field
and then get the chat id(s) from it.
4. Create a configuration file called `config.yml` in the same directory
as the webhook script that looks like this:
```yml
---
target: telegram
slack:
  token: "<SLACK_TOKEN>"
telegram:
  bot_token: "<TELEGRAM_BOT_TOKEN>"
  channel_mapping:
    some-slack-channel: <SOME_CHAT_ID>
    another-slack-channel: <ANOTHER_CHAT_ID>
```
* The Slack token can be anything, whatever you enter here needs to be configured
  as the token in the application that will be configured to send webhooks to the Slack
  webhook receiver.
* The Telegram bot token needs to be a valid Telegram bot token so that the webhook
  can send the notifications to Telegram (see point 5 above).
* The Slack channels under `channel_mapping` need to be valid Slack channel names that
  are configured in the application that will be posting data to the webhook receiver, and
  the Telegram chat id(s) need to be the Telegram chat id(s) that you obtain in point (2)
  and (3) above.

### Discord prerequisites

1. [Create a new Discord Bot](https://discordpy.readthedocs.io/en/stable/discord.html)
   and add the bot to your Discord server.
2. Create your Discord text channels where you want to receive your Spinnaker
   notifications.
3. Get the list of your Discord channel id's by going to `Discord Settings`, then `Advanced`
   and toggling `Developer Mode` to `ENABLED`, and then right-clicking on each of your
   channels and clicking `Copy ID`.
4. Create a configuration file called `config.yml` in the same directory
   as the webhook script that looks like this:
```yml
---
target: discord
slack:
  token: "<SLACK_TOKEN>"
discord:
  bot_token: "<DISCORD_BOT_TOKEN>"
  authors:
    jenkins:
      name: Jenkins
      icon_url: https://example.com/jenkins-icon.png
    spinnaker:
      name: Spinnaker
      icon_url: https://example.com/spinnaker-logo-png
    python:
      name: Python
      icon_url: https://dexample.com/python-logo.png
  channel_mapping:
    some-slack-channel: <SOME_CHANNEL_ID>
    another-slack-channel: <ANOTHER_CHANNEL_ID>
```
* The Slack token can be anything, whatever you enter here needs to be configured
  as the token in the application that will be configured to send webhooks to the Slack
  webhook receiver.
* The `authors` section is optional, the author will default to `Spinnaker` if this is
not set, otherwise the author details are used to look up the author of the `icon_emoji`
field in the Slack payload, eg. `"icon_emoji: ":jenkins:"` will use the `name` and
`icon_url` for the `jenkins` author.
* The Discord bot token needs to be a valid Discord bot token so that the webhook
  can send the notifications to Discord (see point 1 above).
* The Slack channels under `channel_mapping` need to be valid Slack channel names that
  are configured in the application that will be posting data to the webhook receiver, and
  the Discord channel id(s) need to be the Discord channel id(s) that you obtain in point
  (3) above.

### Slack prerequisites

1. [Create a new Slack App](https://api.slack.com/start).
2. Create your Slack channels where you want to receive your Spinnaker notifications.
3. Configure Spinnaker to send notifications to those channels.
4. Create a configuration file called `config.yml` in the same directory
   as the webhook script that looks like this:
```yml
---
target: slack
slack:
  token: "<SLACK_TOKEN>"
```

### Webex prerequisites

1. [Create a new Webex App](https://developer.webex.com/my-apps).
2. Take note of your Bot token and the bot email address.
3. Create your spaces/rooms where you want to receive your Spinnaker notifications.
4. Add your bot to each of the spaces/rooms where you want to receive your Spinnaker
   notifications by inviting it by the email address you noted down in point (2).
5. Configure Spinnaker to send notifications to those spaces/rooms.
6. Get your room id(s) by running the following curl command:
```bash
curl -s -X GET \
  -H "Authorization: Bearer <INSERT_BOT_TOKEN" \
  https://webexapis.com/v1/memberships | jq
```
* This assumes you have `jq` installed. Omit the `| jq` part of the command if you
  don't have it installed and paste the JSON into a [JSON formatter](
  https://jsonformatter.curiousconcept.com/).
7. Create a configuration file called `config.yml` in the same directory
   as the webhook script that looks like this:
```yml
---
target: webex
slack:
  token: "<SLACK_TOKEN>"
webex:
  bot_token: "<WEBEX_BOT_TOKEN>"
  channel_mapping:
    some-slack-channel: <SOME_ROOM_ID>
    another-slack-channel: <ANOTHER_ROOM_ID>
```
* The Slack token can be anything, whatever you enter here needs to be configured
  as the token in the application that will be configured to send webhooks to the Slack
  webhook receiver.
* The Webex bot token needs to be a valid Webex bot token so that the webhook
  can send the notifications to Webex (see point 1 and 2 above).
* The Slack channels under `channel_mapping` need to be valid Slack channel names that
  are configured in the application that will be posting data to the webhook receiver, and
  the Webex room id(s) need to be the Webex channel id(s) that you obtain in point
  (3) above.

## Spinnaker Configuration

Assuming you are using [Halyard](https://github.com/spinnaker/halyard) to
manage your Spinnaker deployment:
```bash
hal config notification slack edit \
  --base-url https://1d602d00.execute-api.us-east-1.amazonaws.com/production \
  --force-use-incoming-webhook
```

## Testing your Webhook

1. Run the webhook receiver from your terminal.
```bash
python3 spinnaker_webhooks.py
```
2. Open a new terminal window and use [ngrok](https://ngrok.com/) to create
a URL that is publically accessible through the internet by creating a tunnel
to the webhook receiver that is running on your local machine.
```bash
ngrok http 8090
```
4. Note that the ngrok URL will change if you stop ngrok and run it again,
   so keep it running in a separate terminal window, otherwise you will not
   be able to test your webhook successfully.
5. Update your Spinnaker webhook configuration to the URL that is displayed
while ngrok is running **(be sure to use the https one)**.
6. Trigger a Spinnaker Pipeline build to trigger the notification webhooks.
7. Check your application channels that you crated for your Spinnaker notifications
that have the bot running within them.

## Deploy to AWS Lambda

1. Create a Python 3.9 Virtual Environment:
```bash
python3 -m venv venv/py3.9
source venv/py3.9/bin/activate
```
2. Upgrade pip.
```bash
python3 -m pip install --upgrade pip
```
3. Install the Python dependencies that are required by the Webhook receiver:
```bash
pip3 install -r requirements.txt
```
4. Create a file called `zappa_settings.json` and insert the JSON content below
to configure your AWS Lambda deployment:
```json
{
    "production": {
        "app_function": "spinnaker_webhooks.app",
        "aws_region": "us-east-1",
        "profile_name": "default",
        "project_name": "spinnaker-webhook",
        "runtime": "python3.9",
        "s3_bucket": "spinnaker-webhooks"
    }
}
```
5. Use [Zappa](https://github.com/Zappa/Zappa) to deploy your Webhook
to AWS Lambda (this is installed as part of the dependencies above):
```bash
zappa deploy
```
6. Take note of the URL that is returned by the `zappa deploy` command,
eg. `https://1d602d00.execute-api.us-east-1.amazonaws.com/production`
   (obviously use your own and don't copy and paate this one, or your
Webhook will not work).

**NOTE:** If you get the following error when running the `zappa deploy` command:

<pre>
botocore.exceptions.ClientError:
An error occurred (IllegalLocationConstraintException) when calling
the CreateBucket operation: The unspecified location constraint
is incompatible for the region specific endpoint this request was sent to.
</pre>

This error usually means that your S3 bucket name is not unique, and that you
should change it to something different, since the S3 bucket names are not
namespaced and are global for everyone.

7. Check the status of the API Gateway URL that was created by zappa:
```bash
zappa status
```
8. Test your webhook by making a curl request to the URL that was returned
by `zappa deploy`:
```
curl https://1d602d00.execute-api.us-east-1.amazonaws.com/production
```
You should expect the following response:
```json
{"status":"ok"}
```
9. Update your Webhook URL in Spinnaker to the one returned by the
`zappa deploy` command.
