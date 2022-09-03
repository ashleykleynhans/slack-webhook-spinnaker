# Slack Compatible API Webhook Receiver to Send Telegram Notifications for Spinnaker

## Background

[Spinnaker](https://spinnaker.io/) supports sending various types of notifications
to various different kinds of applications through the [Echo](
https://github.com/spinnaker/echo) microservice.

However,  [Echo](https://github.com/spinnaker/echo) does not currently support sending
Telegram notifications.

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
5. [Create a new Telegram Bot](https://core.telegram.org/bots#creating-a-new-bot)
and take note of the Bot Token.
6. Create two new Telegram channels, one for **warnings** and one for
**errors** and add the bot into them as an Admin user. These channels can
either be public or private, if they are public, the CHAT ID will be in the
format of `@my_channel` and if they are private, the CHAT ID will be in the
format of `-1000000000000`.
7. If you created private channels, you need to obtain the CHAT IDs for the
channels by running the following curl command:
```
curl https://api.telegram.org/<TELEGRAM_BOT_TOKEN>/getUpdates
```
This will output a JSON response, where you need to look for the `my_chat_member` field
and then get the chat id(s) from it.
8. Create a configuration file called `config.yml` in the same directory
as the webhook script that looks like this:
```yml
---
slack:
   token: "<SLACK_TOKEN>"
telegram:
   bot_token: "<TELEGRAM_BOT_TOKEN>"
   channels:
      some_telegram_channel_name: <SOME_CHAT_ID>
      another_telegram_channel_name: <ANOTHER_CHAT_ID>

channel_mapping:
   some-slack-channel: some_telegram_channel_name
   another-slack-channel: another_telegram_channel_name
```
* The Slack token can be anything, whatever you enter here needs to be configured
as the token in the application that will be configured to send webhooks to the Slack
webhook receiver.
* The Telegram bot token needs to be a valid Telegram bot token so that the webook
can send the notifications to Telegram (see point 5 above).
* The Telegram channel names, can be anything you want, they are only used to assign
meaningful naames to the Telegram chat ids.
* The Slack channels under `channel_mapping` need to be valid Slack channel names that
are configured in the application that will be posting data to the webhook receiver, and
the telegram channel names are to link to the Telegram chat ids as configured in the
previous bullet point.

## Spinnaker Configuration

```
TODO
```

## Testing your Webhook

1. Run the webhook receiver from your terminal.
```bash
python3 telegram_webhooks.py
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
7. Check your Telegram channels that you crated for your Spinnaker notifications
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
        "app_function": "telegram_webhooks.app",
        "aws_region": "us-east-1",
        "profile_name": "default",
        "project_name": "spinnaker-webhook",
        "runtime": "python3.9",
        "s3_bucket": "spinnaker-telegram-webhooks"
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
