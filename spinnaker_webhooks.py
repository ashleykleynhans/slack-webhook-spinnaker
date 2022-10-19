#!/usr/bin/env python3
import sys
import argparse
import yaml
import re
import requests
from flask import Flask, request, jsonify, make_response


SUPPORTED_PLATFORMS = [
    'discord',
    'slack',
    'telegram',
    'webex'
]


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


def substitute_hyperlinks(text, link_format='html'):
    pattern = '(<(https?:\/\/.*?)\|(.*?)>)'
    matches = re.findall(pattern, text)

    if matches:
        for match in matches:
            link_original = match[0]
            link_actual = match[1]
            link_text = match[2]

            if link_format == 'html':
                link_new = f'<a href="{link_actual}">{link_text}</a>'
            elif link_format == 'markdown':
                link_new = f'[{link_text}]({link_actual})'
            else:
                raise Exception(f'Unsupported link format: {link_format}')

            text = text.replace(link_original, link_new)

    return text


def send_discord_notification(channel_id, slack_payload):
    color_map = {
        'green': '#008000',
        'gray': '#808080',
        'red': '#FF0000',
        'blue': '#0000FF',
        'black': '#000000',
        'yellow': '#FFFF00',
        'maroon': '#800000',
        'purple': '#800080',
        'olive': '#808000',
        'silver': '#C0C0C0',
        'gold': '#FFD700',
        'pink': '#FFC0CB',
        'coral': '#FF7F50',
        'brown': '#A52A2A',
        'indigo': '#4B0082',
        'aqua': '#00FFFF',
        'cyan': '#00FFFF',
        'lime': '#00FF00',
        'teal': '#008080',
        'navy': '#000080',
        'sienna': '#A0522D',
        'good': '#2EB67D',
        'warning': '#ECB22E',
        'danger': '#E01E5A',
    }

    bot_url = f'https://discordapp.com/api/channels/{channel_id}/messages'
    discord_bot_token = config['discord']['bot_token']
    embeds = []

    if 'authors' in config['discord'] and 'default' in config['discord']['authors']:
        icon_url = config['discord']['authors']['default']['icon_url']
        icon_type = config['discord']['authors']['default']['name']
    else:
        icon_url = 'https://avatars0.githubusercontent.com/u/7634182?s=200&v=4'
        icon_type = 'Spinnaker'

    if 'icon_emoji' in slack_payload and 'authors' in config['discord']:
        authors = config['discord']['authors']
        icon_emoji = slack_payload['icon_emoji'].replace(':', '')

        if icon_emoji in authors:
            author = authors[icon_emoji]
            icon_url = author['icon_url']
            icon_type = author['name']

    for attachment in slack_payload['attachments']:
        if 'title' in attachment.keys():
            title = substitute_hyperlinks(attachment['title'])
        else:
            title = ''

        embed = {
            'title': title,
            'type': 'rich',
            'description': substitute_hyperlinks(attachment['fallback'], 'markdown'),
            'author': {
                'name': icon_type,
                'icon_url': icon_url
            }
        }

        if 'color' in attachment.keys():
            if attachment['color'] in color_map:
                color = color_map[attachment['color']]
            else:
                color = attachment['color']

            color = color[1:]
            color = int(color, 16)
        else:
            color = None

        if color:
            embed['color'] = color

        embeds.append(embed)

    payload = {
        'embeds': embeds
    }

    return requests.post(
        url=bot_url,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bot {discord_bot_token}'
        },
        json=payload
    )


def send_telegram_notification(chat_id, slack_payload):
    telegram_bot_token = config['telegram']['bot_token']
    bot_url = f'https://api.telegram.org/bot{telegram_bot_token}/sendMessage'
    msg_txt = ''

    for attachment in slack_payload['attachments']:
        if 'title' in attachment.keys():
            title = substitute_hyperlinks(attachment['title'])
            msg_txt += f'<b>{title}</b>\n'

        text = substitute_hyperlinks(attachment['fallback'])
        msg_txt += f'{text}'

    return requests.post(
        url=bot_url,
        data={
            'chat_id': chat_id,
            'parse_mode': 'html',
            'text': msg_txt
        }
    )


def send_slack_notification(slack_payload):
    return requests.post(
        url='https://slack.com/api/chat.postMessage',
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {slack_token}'
        },
        json=slack_payload
    )


def send_webex_notification(room_id, slack_payload):
    webex_bot_token = config['webex']['bot_token']
    bot_url = 'https://webexapis.com/v1/messages'
    msg_txt = ''

    for attachment in slack_payload['attachments']:
        if 'title' in attachment.keys():
            title = substitute_hyperlinks(attachment['title'], 'markdown')
            msg_txt += f'**{title}**\n'

        text = substitute_hyperlinks(attachment['fallback'], 'markdown')
        msg_txt += f'{text}'

    return requests.post(
        url=bot_url,
        headers={
            'Authorization': f'Bearer {webex_bot_token}'
        },
        data={
            'roomId': room_id,
            'markdown': msg_txt
        }
    )


def discord_handler():
    if 'discord' not in config:
        return make_response(jsonify(
            {
                'status': 'error',
                'msg': "'discord' section not found in config"
            }
        ), 404)

    if 'bot_token' not in config['discord']:
        return make_response(jsonify(
            {
                'status': 'error',
                'msg': "'bot_token' section not found in 'discord' section of config"
            }
        ), 404)

    slack_payload = request.get_json()

    if 'channel' in slack_payload:
        slack_channel = slack_payload['channel']
        # Drop the # prefix from the slack channel
        slack_channel = slack_channel[1:]
    elif 'default_channel' in config['slack']:
        slack_channel = config['slack']['default_channel']
    else:
        return make_response(jsonify(
            {
                'status': 'error',
                'msg': "'default_channel' section not found in 'slack' section of config"
            }
        ), 404)

    channel_mapping = config['discord']['channel_mapping']

    if slack_channel in channel_mapping:
        discord_channel_id = channel_mapping[slack_channel]
    else:
        return make_response(jsonify(
            {
                'status': 'error',
                'msg': f'Slack channel {slack_channel} not found in channel_mapping config'
            }
        ), 404)

    response = send_discord_notification(discord_channel_id, slack_payload)
    discord_response = response.json()

    if response.status_code != 200:
        return make_response(jsonify(
            {
                'status': 'error',
                'msg': f'Failed to send Discord notification to channel id: {discord_channel_id}',
                'detail': discord_response
            }
        ), 500)

    return jsonify(discord_response)


def telegram_handler():
    if 'telegram' not in config:
        return make_response(jsonify(
            {
                'status': 'error',
                'msg': "'telegram' section not found in config"
            }
        ), 404)

    if 'channel_mapping' not in config['telegram']:
        return make_response(jsonify(
            {
                'status': 'error',
                'msg': "'channel_mapping' section not found in 'telegram' section of config"
            }
        ), 404)

    if 'bot_token' not in config['telegram']:
        return make_response(jsonify(
            {
                'status': 'error',
                'msg': "'bot_token' section not found in 'telegram' section of config"
            }
        ), 404)

    slack_payload = request.get_json()
    slack_channel = slack_payload['channel']
    # Drop the # prefix from the slack channel
    slack_channel = slack_channel[1:]
    channel_mapping = config['telegram']['channel_mapping']

    if slack_channel in channel_mapping:
        telegram_chat_id = channel_mapping[slack_channel]
    else:
        return make_response(jsonify(
            {
                'status': 'error',
                'msg': f'Slack channel {slack_channel} not found in channel_mapping config'
            }
        ), 404)

    response = send_telegram_notification(telegram_chat_id, slack_payload)
    telegram_response = response.json()

    if response.status_code != 200 or not telegram_response['ok']:
        return make_response(jsonify(
            {
                'status': 'error',
                'msg': f'Failed to send Telegram notification to chat id: {telegram_chat_id}',
                'detail': telegram_response
            }
        ), 500)

    return jsonify(telegram_response)


def webex_handler():
    if 'webex' not in config:
        return make_response(jsonify(
            {
                'status': 'error',
                'msg': "'webex' section not found in config"
            }
        ), 404)

    if 'channel_mapping' not in config['webex']:
        return make_response(jsonify(
            {
                'status': 'error',
                'msg': "'channel_mapping' section not found in 'webex' section of config"
            }
        ), 404)

    if 'bot_token' not in config['webex']:
        return make_response(jsonify(
            {
                'status': 'error',
                'msg': "'bot_token' section not found in 'webex' section of config"
            }
        ), 404)

    slack_payload = request.get_json()
    slack_channel = slack_payload['channel']
    # Drop the # prefix from the slack channel
    slack_channel = slack_channel[1:]
    channel_mapping = config['webex']['channel_mapping']

    if slack_channel in channel_mapping:
        webex_room_id = channel_mapping[slack_channel]
    else:
        return make_response(jsonify(
            {
                'status': 'error',
                'msg': f'Slack channel {slack_channel} not found in channel_mapping config'
            }
        ), 404)

    response = send_webex_notification(webex_room_id, slack_payload)
    webex_response = response.json()

    if response.status_code != 200:
        return make_response(jsonify(
            {
                'status': 'error',
                'msg': f'Failed to send Webex notification to room id: {webex_room_id}',
                'detail': webex_response
            }
        ), 500)

    return jsonify(webex_response)


def slack_handler():
    slack_payload = request.get_json()
    response = send_slack_notification(slack_payload)
    slack_response = response.json()

    if response.status_code != 200:
        return make_response(jsonify(
            {
                'status': 'error',
                'msg': 'Failed to send Slack notification',
                'detail': slack_response
            }
        ), 500)

    return jsonify(slack_response)


config = load_config()

if 'slack' not in config:
    print("'slack' section not found in config")
    sys.exit(1)

if 'token' not in config['slack']:
    print("'token' not found in 'slack' section of config")
    sys.exit(1)

slack_token = config['slack']['token']
app = Flask(__name__)


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
    ), 500)


@app.route('/')
def ping():
    return make_response(jsonify(
        {
            'status': 'ok'
        }
    ), 200)


@app.route(f'/{slack_token}', methods=['POST'])
def webhook_handler():
    if 'target' not in config:
        return make_response(jsonify(
            {
                'status': 'error',
                'msg': '"target" section not found in config'
            }
        ), 404)

    if config['target'] == 'telegram':
        return telegram_handler()
    elif config['target'] == 'discord':
        return discord_handler()
    elif config['target'] == 'slack':
        return slack_handler()
    elif config['target'] == 'webex':
        return webex_handler()
    else:
        return make_response(jsonify(
            {
                'status': 'error',
                'msg': 'No supported notification platform found in config, ' +
                       'ensure that "target" is set to a supported platform type.'
            }
        ), 404)


if __name__ == '__main__':
    args = get_args()

    if 'target' in config:
        target = config['target']

        if target not in SUPPORTED_PLATFORMS:
            print(f'Unsupported target notification platform: {target}')
            sys.exit(1)
        else:
            print(f'Target notification platform: {target.title()}')

    app.run(
        host=args.host,
        port=args.port
    )
