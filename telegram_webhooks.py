#!/usr/bin/env python3
import sys
import argparse
import yaml
import re
import requests
from flask import Flask, request, jsonify, make_response


def get_args():
    parser = argparse.ArgumentParser(
        description='Slack Compatible API Webhook Receiver to Send Telegram Notifications'
    )

    parser.add_argument(
        '-p', '--port',
        help='Port to listen on',
        type=int,
        default=8090
    )

    parser.add_argument(
        '-H', '--host',
        help='Host to bind to',
        default='0.0.0.0'
    )

    return parser.parse_args()


def load_config():
    try:
        config_file = 'config.yml'

        with open(config_file, 'r') as stream:
            return yaml.safe_load(stream)
    except FileNotFoundError:
        print(f'ERROR: Config file {config_file} not found!')
        sys.exit()


def substitute_hyperlinks(text):
    pattern = '(<(https?:\/\/.*?)\|(.*?)>)'
    matches = re.findall(pattern, text)

    if matches:
        for match in matches:
            link_original = match[0]
            link_actual = match[1]
            link_text = match[2]
            link_new = f'<a href="{link_actual}">{link_text}</a>'
            text = text.replace(link_original, link_new)

    return text


def send_telegram_notification(chat_id, slack_payload):
    telegram_bot_token = config['telegram']['bot_token']
    attachment = slack_payload['attachments'][0]
    msg_txt = ''

    if 'title' in attachment.keys():
        title = substitute_hyperlinks(attachment['title'])
        msg_txt += f'<b>{title}</b>\n'

    text = substitute_hyperlinks(attachment['fallback'])
    msg_txt += f'{text}'

    msg_data = {
        'chat_id': chat_id,
        'parse_mode': 'html',
        'text': msg_txt
    }

    bot_url = f'https://api.telegram.org/bot{telegram_bot_token}/sendMessage'
    req = requests.post(url=bot_url, data=msg_data)
    return req.json()


app = Flask(__name__)
config = load_config()
slack_token = config['slack']['token']


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify(
        {
            'status': 'error',
            'msg': f'{request.url} not found',
            'detail': str(error)
        }
    ), 404)


@app.errorhandler(500)
def internal_server_error(error):
    return make_response(jsonify(
        {
            'status': 'error',
            'msg': 'Internal Server Error',
            'detail': str(error)
        }
    ), 404)


@app.route('/')
def ping():
    return make_response(jsonify(
        {
            'status': 'ok'
        }
    ), 200)


@app.route(f'/{slack_token}', methods=['POST'])
def webhook_handler():
    slack_payload = request.get_json()
    slack_channel = slack_payload['channel']
    # Drop the # prefix from the slack channel
    slack_channel = slack_channel[1:]
    telegram_channels = config['telegram']['channels']
    channel_mapping = config['channel_mapping']
    telegram_channel_name = channel_mapping[slack_channel]
    telegram_chat_id = telegram_channels[telegram_channel_name]
    telegram_response = send_telegram_notification(telegram_chat_id, slack_payload)
    return jsonify(telegram_response)


if __name__ == '__main__':
    SLACK_TOKEN = '1233'
    args = get_args()

    app.run(
        host=args.host,
        port=args.port
    )
