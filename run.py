# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

__author__ = 'ufian'

import os
import re
import time
import logging
import random
import datetime as dt
from collections import defaultdict

import requests as r
from slackclient import SlackClient


from websocket import WebSocketConnectionClosedException
from socket import error as SocketError

try:
    from slackclient._client import SlackNotConnected # not actually used, see https://github.com/slackapi/python-slackclient/issues/36
    from slackclient._server import SlackConnectionError
except ImportError:
    SlackNotConnected = SocketError
    SlackConnectionError = SocketError

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

class Messages(me.Document):
    meta = {'collection': 'questions'}
    
    timestamp = me.DecimalField(precision=6)
    user = me.StringField()
    data = me.DictField()

class Questions(me.Document):
    meta = {'collection': 'questions'}
    
    user = me.StringField(required=True)
    text = me.StringField(required=True)
    date = me.DateTimeField(required=True)

class User(me.Document):
    meta = {'collection': 'questions'}
    
    user = me.StringField(required=True)
    admin = me.BooleanField(required=True)

def _is_bot_mention(sc, event):
    bot_user_name = sc.server.login_data['self']['id']
    if re.search("@{}".format(bot_user_name), event.get('text', '')):
        return True
    else:
        return False
    
def _is_direct_message(sc, event):
    return event.get('channel').startswith('D')

def _is_question(sc, event):
    msg = event['text']
    msg_lower = msg.lower().rstrip()
    
    if not msg_lower.endswith('?'):
        return False
    
    if _is_bot_mention(sc, event):
        tatarin_aliases = ['<@U74JZCPA5>', '@tatarin']
        return any(msg.startswith(alias) for alias in tatarin_aliases)

    if _is_direct_message(sc, event):
        return True
    
    question_forms = ['вопрос:', 'внимание, вопрос:']
    return any(msg_lower.startswith(form) for form in question_forms)

def _is_list_request(sc, event):
    msg = event['text']
    msg_lower = msg.lower().rstrip()

    if not _is_direct_message(sc, event):
        return False
        
    return 'вопросы' in msg_lower

def _last_date_podcast():
    try:
        feed_url = "https://feeds.feedburner.com/rosnovsky"
        req = r.get(feed_url)
        if req.status_code != 200:
            raise
        
        text = req.text
        pos_start = text.find("<pubDate>")
        pos_end = text.find("</pubDate>")
        if pos_start == -1 or pos_end == -1:
            raise
        
        pos_start += len("<pubDate>")
        str_dt = text[pos_start: pos_end]
        
        if len(str_dt) < len("Sun, 08 Oct 2017 21:56:47"):
            raise
        
        if not str_dt.endswith(" PDT"):
            raise
        
        return dt.datetime.strptime(str_dt[:-4], "%a, %d %b %Y %H:%M:%S") - dt.timedelta(hours=10)

    except:
        return dt.datetime.now() - dt.timedelta(days=60)

def _process_event(event):
    timestamp = event.get('ts')
    user = event.get('user')
    
    if not timestamp or not user:
        return True
    
    if user == u'U74JZCPA5':
        return False
    
    logging.info('Check ts={0} user={1}'.format(timestamp, user))
    if Messages.objects(timestamp=timestamp, user=user).count() > 0:
        logging.info('Skip message')
        return False
    
    m = Messages(
        timestamp=timestamp,
        user=user,
        data=event
    )
    m.save()
    return True


def _question_text(text):
    prefixes = [
        'вопрос:',
        'внимание, вопрос:',
        '<@u74jzcpa5>',
        '@tatarin'
    ]
    
    text_lower = text.lower()
    
    for prefix in prefixes:
        if text_lower.startswith(prefix):
            text = text[len(prefix):].strip()
            text_lower = text_lower[len(prefix):].strip()
            
    return text.strip()


def message_event(sc, event):
    if not _process_event(event):
        return
    
    msg = event['text']
    
    if _is_list_request(sc, event):
        last_dt = _last_date_podcast()
        parts = ['Вопросы с {0}'.format(last_dt.strftime('%d %b %Y %H:%M:%S'))]
        questions = defaultdict(list)
        for q in Questions.objects(user__ne="USLACKBOT", text__endswith='?', date__gt=last_dt).order_by('+date'):
            questions[q.user].append(q)

        cache = set()
        for user, user_q in questions.items():
            list_q = list()
            
            for q in user_q:
                text = _question_text(q.text)
                if text in cache:
                    continue
                if len(text) < 10:
                    continue
                list_q.append(text)
                cache.add(text)


            if list_q:
                parts.append('*Вопросы от* <@{0}>:'.format(user))
                
                for i, q in enumerate(list_q, start=1):
                    parts.append("*{0}*. {1}".format(i, q))
                parts.append('.')
            
            
        if parts[-1] == '.':
            parts = parts[:-1]
            
        return '\n'.join(parts)
        
    if _is_question(sc, event):
        user = event['user']
        if Questions.objects(user=user, date__gt=dt.datetime.now() - dt.timedelta(days=1)).count() >= 3:
            return "Хватит, <@{0}>, присылать вопросы. Татрин советует вернуться завтра.".format(user)
        
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
                sc.rtm_send_message(
                    channel=u'D754XJPGA',
                    message='Restarted {0}'.format(dt.datetime.now()),
                )
                
                while True:
                    try:
                        handle(sc, sc.rtm_read())
                    except:
                        logging.exception('Problem')
                    time.sleep(1)
            else:
                logging.error("Connection Failed, invalid token?")
        except (SocketError, WebSocketConnectionClosedException, SlackConnectionError, SlackNotConnected):
            if not SlackClient(slack_token).rtm_connect():
                logging.exception('Global reconnect problem')
        except:
            logging.exception('Global problem. Recreate app')
            time.sleep(1)


if __name__ == "__main__":
    main()
