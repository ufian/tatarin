# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function


__author__ = 'ufian'

import re
import logging
import datetime as dt
from dateutil import parser as dp
from collections import defaultdict

import requests as r

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

class Podcast(object):
    FEED_URL = "https://feeds.feedburner.com/rosnovsky"
    
    CACHE = None
    CACHE_DT = None
    
    re_pubdate = re.compile('<pubDate>(.*)</pubDate>')
    re_title = re.compile('<title>(.*)</title>')

    def __init__(self):
        self._update_cache()
        self.podcasts = list()
    
    def _update_cache(self):
        if Podcast.CACHE_DT is not None and (dt.datetime.now() - Podcast.CACHE_DT) < dt.timedelta(hours=8):
            return
        
        try:
            req = r.get(Podcast.FEED_URL)
            
            if '<pubDate>' not in req.text:
                return

            Podcast.CACHE = req.text
            Podcast.CACHE_DT = dt.datetime.now()
            
        except:
            return
        
    def _parse_feed(self):
        self.podcasts = list()
        
        if Podcast.CACHE is None:
            return

        parts = Podcast.CACHE.split('<item>')[1:]

        for part in parts:
            pubdate = self.re_pubdate.search(part)
            title = self.re_title.search(part)
            
            if not pubdate or not title:
                continue
    
            pubdate = pubdate.group(1)
            title = title.group(1)

            try:
                pubdate = dp.parse(pubdate)
            except:
                continue
            

            self.podcasts.append((pubdate, title))
                
    def info(self, shift=0):
        self._parse_feed()
        
        if len(self.podcasts) == 0:
            return (dt.datetime.now() - dt.timedelta(days=60), "Feed unavailable")
        
        if shift >= len(self.podcasts):
            return self.podcasts[-1]
        
        return self.podcasts[shift]

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
        shift = 0
        podcast = Podcast()
        podcast_dt, podcast_name = podcast.info(shift)
        
        parts = ['Вопросы с *{0}* ({1})'.format(podcast_name, podcast_dt.strftime('%d %b %Y %H:%M:%S'))]
        questions = defaultdict(list)
        for q in Questions.objects(user__ne="USLACKBOT", text__endswith='?', date__gt=podcast_dt).order_by('+date'):
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
