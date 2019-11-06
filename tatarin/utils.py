# -*- coding: utf-8 -*-

__author__ = 'ufian'

import re

import tatarin


def is_bot_mention(data):
    if tatarin.BOT_ID is None:
        return False

    return bool(re.search("@{}".format(tatarin.BOT_ID), data.get('text', '')))


def is_direct_message(event):
    return event.get('channel').startswith('D')
