# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

__author__ = 'ufian'

import os
import re
import time
import logging
import random
import datetime as dt
from slackclient import SlackClient

import slackbot_settings as config

import mongoengine as me

logger = logging.getLogger(__name__)


def get_connect():
    return me.connect(
        config.DB['db'],
        host=config.DB['host'],
        port=config.DB['port'],
        serverSelectionTimeoutMS=2500
    )


class Questions(me.Document):
    meta = {'collection': 'questions'}
    
    user = me.StringField(required=True)
    text = me.StringField(required=True)
    date = me.DateTimeField(required=True)


def _is_bot_mention(sc, event):
    bot_user_name = sc.server.login_data['self']['id']
    if re.search("@{}".format(bot_user_name), event.get('text', '')):
        return True
    else:
        return False
    
def _is_direct_message(sc, event):
    return event.get('channel').startswith('D')

def message_event(sc, event):
    msg = event['text']
    
    if _is_direct_message(sc, event) and 'вопросы' in msg.lower():
        parts = []
        for q in Questions.objects(user__ne="USLACKBOT", text__endswith='?').order_by('-date').limit(10):
            parts.append(
                '<@{0}>: {1}'.format(q.user, q.text)
            )
            
        return '\n'.join(parts)
        
    
    if (_is_bot_mention(sc, event) and msg.startswith('<@U74JZCPA5>') or _is_direct_message(sc, event)) and msg.endswith('?'):
        q = Questions(
            user=event['user'],
            text=msg,
            date=dt.datetime.now()
        )
        q.save()
        
        return "Принято"

def handle(sc, events):
    for event in events:
        logging.info('Event: {0}'.format(event))
        event_type = event.get('type', 'None')
        if event_type == 'message':
            reply = handle_message(sc, event)
            
            if reply is not None:
                sc.rtm_send_message(
                  channel=event.get('channel'),
                  message=reply,
                )
        
def handle_message(sc, event):
    subtype = event.get('subtype', '')
    
    reply = message_event(sc, event)
        
    return reply


def main():
    log_level = os.getenv("LOG_LEVEL", "INFO") or "INFO"
    logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', level=log_level)
    
    slack_token = getattr(config, "API_TOKEN", os.getenv("SLACK_TOKEN", ""))
    logging.info("token: {}".format(slack_token))
    
    while True:
        try:
            sc = SlackClient(slack_token)
            
            get_connect()
        
            if sc.rtm_connect():
                while True:
                    try:
                        handle(sc, sc.rtm_read())
                    except:
                        logging.exception('Problem')
                    time.sleep(1)
            else:
                logging.error("Connection Failed, invalid token?")
        except:
            logging.exception('Global problem. Recreate app')
            time.sleep(1)


if __name__ == "__main__":
    main()
