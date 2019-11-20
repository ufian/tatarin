from collections import defaultdict

import tatarin
from tatarin.model import Questions, TelegramQuestions
from tatarin.podcast import Podcast
from tatarin.utils import is_direct_message


def _is_history_request(event):
    msg = event['text']
    msg_lower = msg.lower().rstrip()

    if not is_direct_message(event):
        return False

    return 'вопросы' in msg_lower


def _parse_request(event):
    msg = event['text']
    msg_lower = msg.lower().rstrip()

    _, _, data = msg_lower.partition('вопросы')

    data = data.strip().split()
    if len(data) == 0 or len(data[0]) < 2:
        return 'SHIFT', 0
    elif data[0] == 'как' or data[0] == 'пример':
        return 'HELP', "\n".join([
            "Вопросы с 42 подкаста",
            "Вопросы за последние 3 подкаста",
        ])
    elif len(data) >= 3 and data[-1].startswith('подкаст'):
        if data[0] == 'с' or data[0] == 'от':
            return 'NUMBER', int(data[1])
        elif data[0] == 'за':
            return 'SHIFT', int(data[-2]) - 1

    return None, None


def _question_text(text):
    prefixes = [
        'вопрос:',
        'внимание, вопрос:',
        '<@{}>'.format(tatarin.BOT_ID).lower(),
        '@tatarin'
    ]

    text_lower = text.lower()

    for prefix in prefixes:
        if text_lower.startswith(prefix):
            text = text[len(prefix):].strip()
            text_lower = text_lower[len(prefix):].strip()

    return text.strip()


def _add_slack_questions(parts, podcast_dt):
    questions = defaultdict(list)
    for q in Questions.objects(user__ne="USLACKBOT", text__exists=True, date__gt=podcast_dt).order_by('+date'):
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

def _add_telegram_questions(parts, podcast_dt):
    parts.append('Вопросы из *Telegram*')

    questions = defaultdict(list)
    for q in TelegramQuestions.objects(date__gt=podcast_dt).order_by('+date'):
        group_key = q.data.get('from', {}).get('id', None) or q.user
        questions[group_key].append(q)

    cache = set()
    for group_key, user_q in questions.items():
        list_q = list()

        from_name = None

        for q in user_q:
            text = q.data.get('text', "")

            if 'from' in q.data:
                t_from = q.data['from']
                t_name = "{}"
                if 'username' in t_from:
                    t_name = "@" + t_from['username'] + " ({})"

                fl_names = filter(None, [t_from.get('first_name'), t_from.get('last_name')])

                if t_name != "{}" or fl_names:
                    from_name = t_name.format(" ".join(fl_names))

            if text in cache:
                continue
            if len(text) < 10:
                continue
            list_q.append(text)
            cache.add(text)


        if list_q:
            parts.append('*Вопросы от* {0}:'.format(from_name or group_key))

            for i, q in enumerate(list_q, start=1):
                parts.append("*{0}*. {1}".format(i, q))
            parts.append('.')

def _process_podcast(podcast_dt, podcast_name):
    parts = ['Вопросы с *{0}* ({1})'.format(podcast_name, podcast_dt.strftime('%d %b %Y %H:%M:%S'))]

    _add_slack_questions(parts, podcast_dt)
    _add_telegram_questions(parts, podcast_dt)

    if parts[-1] == '.':
        parts = parts[:-1]

    return parts


def handler(data):
    if not _is_history_request(data):
        return None

    q_type, q_param = _parse_request(data)
    if q_type == 'HELP':
        return q_param

    podcast = Podcast()

    if q_type == 'NUMBER':
        podcast_dt, podcast_name = podcast.info_number(q_param)
    elif q_type == 'SHIFT':
        podcast_dt, podcast_name = podcast.info(q_param)
    else:
        podcast_dt, podcast_name = podcast.info()

    parts = _process_podcast(podcast_dt, podcast_name)

    if q_type not in ['NUMBER', 'SHIFT'] or q_param is None or isinstance(q_param, int) and q_param < 1:
        parts.append('.')
        parts.append('Попробуй `вопросы за 2 подкаста`')

    return '\n'.join(parts)
