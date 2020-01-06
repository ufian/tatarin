# -*- coding: utf-8 -*-

__author__ = 'ufian'

import datetime as dt

import tatarin
from tatarin.model import Questions
from tatarin.utils import is_bot_mention, is_direct_message


def _is_question(data):
    msg = data['text']
    msg_lower = msg.lower().rstrip()

    if not (msg_lower.endswith('?') or '? ' in msg_lower):
        return False

    if is_bot_mention(data):
        tatarin_aliases = ['<@{}>'.format(tatarin.BOT_ID), '@tatarin']
        return any(msg.startswith(alias) for alias in tatarin_aliases)

    if is_direct_message(data):
        return True

    question_forms = ['вопрос:', 'внимание, вопрос:']
    return any(msg_lower.startswith(form) for form in question_forms)


def handler(data):
    if not _is_question(data):
        return None

    msg = data['text']
    user = data['user']

    if Questions.objects(user=user, date__gt=dt.datetime.now() - dt.timedelta(days=1)).count() >= 3:
        return "Хватит, <@{0}>, присылать вопросы. Татарин советует вернуться завтра.".format(user)

    url = 'https://podtema.slack.com/archives/{0}/p{1}'.format(data['channel'], data['ts'].replace('.', ''))

    q = Questions(
        user=data['user'],
        text='{0} ({1})'.format(msg, url),
        date=dt.datetime.now()
    )
    q.save()

    return "Принято. Большое татарское спасибо!"
