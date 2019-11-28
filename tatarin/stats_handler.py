# -*- coding: utf-8 -*-

__author__ = 'ufian'

from tatarin.model import Messages
from tatarin.utils import is_direct_message


def _is_stats_request(data):
    msg = data['text']
    msg_lower = msg.lower().strip()

    if not is_direct_message(data):
        return False

    return 'статистика' == msg_lower

def get_stats():
    stats = Messages.objects(data__exists=True).aggregate(
        {"$group": {
            "_id": "$user",
            "count": {"$sum": 1}
        }},
        {"$sort": {
            "count": -1
        }}
    )

    lines = [
        "<@{0}>: {1} сообщений".format(row["_id"], row["count"])
        for row in stats
    ]

    return "\n".join(lines)


def handler(data):
    if not _is_stats_request(data):
        return None

    return get_stats()
