# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function


__author__ = 'ufian'

import os
import logging
import json
import asyncio
import uvloop
import sys

from slack import RTMClient, WebClient

from tatarin.model import get_connect
import tatarin.bot
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
    
    @RTMClient.run_on(event="open")
    def open_handler(web_client: WebClient, **kwargs):
        try:
            bot_info = web_client.auth_test(token=slack_token)
            assert bot_info["ok"]
            assert bot_info["user_id"]
            tatarin.bot.BOT_ID = bot_info["user_id"]
        except Exception as e:
            logging.exception("error:", exc_info=sys.exc_info())


    @RTMClient.run_on(event="message")
    def message_handler(data, web_client, **kwargs):
        try:
            logging.info('Payload: {0}'.format(json.dumps(data, indent=2)))
        
            reply = message_event(data)
            logging.info("Reply: {0} {1}".format(reply, data.get('channel')))
            if reply is not None:
                web_client.chat_postMessage(
                    channel=data.get('channel'),
                    text=reply
                )
        except Exception as e:
            logging.exception("error:", exc_info=sys.exc_info())

    sc = RTMClient(token=slack_token, loop=loop, auto_reconnect=True)
    sc.start()


if __name__ == "__main__":
    main()
