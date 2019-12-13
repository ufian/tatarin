from tatarin.utils import is_direct_message


def _is_spy_request(event):
    msg = event['text']
    msg_lower = msg.lower().rstrip()

    if not is_direct_message(event):
        return False

    return msg_lower.startswith("скажи в <") \
           or msg_lower.startswith("скажи <") \
           or msg_lower.startswith("<")


def _parse_request(event):
    msg = event['text']

    _, _, part = msg.partition('<')
    chat, _, message = part.partition('> ')
    chat, _, _ = chat.partition('|')


    return chat, message


def handler(data):
    if not _is_spy_request(data):
        return None

    chat, message = _parse_request(data)

    if len(message) < 1:
        return None

    return chat, message
