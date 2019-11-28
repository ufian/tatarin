# -*- coding: utf-8 -*-

__author__ = 'ufian'

from tatarin.model import Messages
from tatarin.utils import is_direct_message


def _is_stats_request(data):
    msg = data['text']
    msg_lower = msg.lower().strip()

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

def get_local_stats(data):
    user = data['user']
    channel = data['channel']
    stats = Messages.objects(data__exists=True, user=user).aggregate(
        {"$match": {"data.channel": channel}},
        {"$group": {
            "_id": "$user",
            "count": {"$sum": 1}
        }},
        {"$sort": {
            "count": -1
        }}
    )

    lines = [
        "<@{0}> отправил(а) {1} сообщений в этот чат".format(row["_id"], row["count"])
        for row in stats
    ]

    return "\n".join(lines)


def handler(data):
    if not _is_stats_request(data):
        return None

    if is_direct_message(data):
        return get_stats()

    return get_local_stats(data)