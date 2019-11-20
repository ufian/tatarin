import slackbot_settings as config
import mongoengine as me

def get_connect():
    return me.connect(config.DB['db'], host=config.DB['host'], port=config.DB['port'], serverSelectionTimeoutMS=2500)


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


class TelegramQuestions(me.Document):
    meta = {'collection': 'telegram'}

    date = me.DateTimeField(required=True)
    user = me.StringField()
    data = me.DictField()
