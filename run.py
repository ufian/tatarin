# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

__author__ = 'ufian'

import os
import logging
import json
import asyncio
import uvloop
import random
import sys
import time

from slack import RTMClient, WebClient

from tatarin.model import get_connect
import tatarin
from tatarin.bot import message_event
import slackbot_settings as config

logger = logging.getLogger(__name__)
loop = asyncio.get_event_loop()
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

def main():
    log_level = os.getenv("LOG_LEVEL", "INFO") or "INFO"
    logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', level=log_level)

    slack_token = getattr(config, "API_TOKEN", os.getenv("SLACK_TOKEN", ""))
    logging.info("token: {}".format(slack_token))

    get_connect()

    typing_storage = dict()

    @RTMClient.run_on(event="open")
    def open_handler(web_client: WebClient, **kwargs):
        try:
            bot_info = web_client.auth_test(token=slack_token)
            assert bot_info["ok"]
            assert bot_info["user_id"]
            tatarin.BOT_ID = bot_info["user_id"]
        except Exception as e:
            logging.exception("error:", exc_info=sys.exc_info())


    @RTMClient.run_on(event="message")
    def message_handler(data, web_client: WebClient, **kwargs):
        try:
            logging.info('Payload: {0}'.format(json.dumps(data, indent=2)))
        
            reply = message_event(data)
            logging.info("Reply: {0} {1}".format(reply, data.get('channel')))

            if reply is not None:
                if isinstance(reply, tuple):
                    chat, message = reply
                else:
                    chat, message = data.get('channel'), reply

                chat = chat.lstrip("#")

                web_client.chat_postMessage(
                    channel=chat,
                    text=message
                )
        except Exception as e:
            logging.exception("error:", exc_info=sys.exc_info())

    @RTMClient.run_on(event="channel_created")
    def channel_created_handler(data, web_client: WebClient, **kwargs):
        try:
            logging.info('Payload: {0}'.format(json.dumps(data, indent=2)))

            channel = data['channel']
            if hasattr(config, "DIRECT_MESSAGE"):
                web_client.chat_postMessage(
                    channel=config.DIRECT_MESSAGE,
                    text="Created channel #{}".format(channel['name'])
                )

        except Exception as e:
            logging.exception("error:", exc_info=sys.exc_info())

    @RTMClient.run_on(event="user_typing")
    def user_typing_handler(data, web_client: WebClient, **kwargs):
        tempaltes = [
            "<@{}> Ты там поэму что ли строчишь?",
            "<@{}> Я ожидаю что-то очень интересное",
            "<@{}> Ну сколько можно! Я устал ждать твоего сообщения"
        ]

        try:
            logging.info('Payload user_typing: {0}'.format(json.dumps(data, indent=2)))

            key = (data['channel'], data['user'])
            story = typing_storage.get(key, {})

            current = time.time()
            started = story.get('started', current)
            notify = story.get('notify', False)
            prev = story.get('prev', current)

            if (current - prev) > 13:
                typing_storage[key] = {
                    'prev': current,
                    'started': current,
                    'notify': False
                }
                return

            if (current - started) > 3 * 60 and not notify:
                notify = True

                channel, user = key
                web_client.chat_postMessage(
                    channel=channel,
                    text=random.choice(tempaltes).format(user)
                )

            typing_storage[key] = {
                'prev': current,
                'started': started,
                'notify': notify
            }

        except Exception as e:
            logging.exception("error:", exc_info=sys.exc_info())


    sc = RTMClient(token=slack_token, loop=loop, auto_reconnect=True)
    sc.start()


if __name__ == "__main__":
    main()
