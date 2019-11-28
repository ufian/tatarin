# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

__author__ = 'ufian'

import logging
import sys

from tatarin.model import Messages
import tatarin.history_request_handler as history_request_handler
import tatarin.question_handler as question_handler
import tatarin.stats_handler as stats_handler

HANDLERS = [
    history_request_handler.handler,
    stats_handler.handler,
    question_handler.handler
]


logger = logging.getLogger(__name__)


def _process_event(event):
    timestamp = event.get('ts')
    user = event.get('user')

    if not timestamp or not user:
        return False

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


def message_event(event):
    if not _process_event(event):
        return

    for handler in HANDLERS:
        try:
            result = handler(event)
            if result is not None:
                return result

        except:
            logging.exception("error in handler:", exc_info=sys.exc_info())
