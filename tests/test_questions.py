import unittest

import mongoengine as me

import tatarin.bot
from tatarin.bot import message_event
from tatarin.model import Questions
from mongomock.store import DatabaseStore


class TestQuestions(unittest.TestCase):
    BOT_ID = "TESTID"
    COLLECTION = "questions"

    MONGO_MOCK = None

    @classmethod
    def setUpClass(cls):
        tatarin.BOT_ID = cls.BOT_ID
        conn = me.connect('mongoenginetest', host='mongomock://localhost')
        cls.MONGO_MOCK: DatabaseStore = conn.mongoenginetest
        cls.MONGO_MOCK.create_collection(cls.COLLECTION)
        
    @classmethod
    def tearDownClass(cls):
        me.disconnect()

    def setUp(self):
        super(TestQuestions, self).setUp()
        
        self.MONGO_MOCK[self.COLLECTION].drop()
        self.MONGO_MOCK.create_collection(self.COLLECTION)


    def test_simple(self):
        assert Questions.objects(text__exists=True).count() == 0
    
        message = "<@{}> question?".format(self.BOT_ID)
    
        data = {"client_msg_id": "0ebe05ca-a41f-4174-8d19-0a3e34b0e0d5", "suppress_notification": False,
            "text": message, "user": "U36UPATB6", "team": "T37A8AJBZ", "user_team": "T37A8AJBZ",
            "source_team": "T37A8AJBZ", "channel": "C4V5A0E3W", "event_ts": "1572364286.379400",
            "ts": "1572364286.379400"}
    
        reply = message_event(event=data)
        assert reply, "Reply isn't empty"
    
        assert Questions.objects(text__exists=True).count() == 1

    def test_trailing_sentence(self):
        assert Questions.objects(text__exists=True).count() == 0
    
        message = "<@{}> Росновский, когда подкаст? Опять до последнего тянешь!".format(self.BOT_ID)
    
        data = {"client_msg_id": "0ebe05ca-a41f-4174-8d19-0a3e34b0e0d5", "suppress_notification": False,
            "text": message, "user": "U36UPATB6", "team": "T37A8AJBZ", "user_team": "T37A8AJBZ",
            "source_team": "T37A8AJBZ", "channel": "C4V5A0E3W", "event_ts": "1572364286.379400",
            "ts": "1572364286.379400"}
    
        reply = message_event(event=data)
        assert reply, "Reply isn't empty"

        assert Questions.objects(text__exists=True).count() == 1
