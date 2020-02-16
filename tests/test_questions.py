import unittest

import mongoengine as me

import tatarin
from tatarin.bot import message_event
from tatarin.model import Questions
from mongomock.store import DatabaseStore
from mongoengine.pymongo_support import count_documents


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
        self.db_collection = self.MONGO_MOCK.create_collection(self.COLLECTION)

    def _test_success(self, message):
        assert count_documents(self.db_collection, {'text': {'$exists': True}}) == 0

        data = {"client_msg_id": "0ebe05ca-a41f-4174-8d19-0a3e34b0e0d5", "suppress_notification": False,
                "text": message, "user": "U36UPATB6", "team": "T37A8AJBZ", "user_team": "T37A8AJBZ",
                "source_team": "T37A8AJBZ", "channel": "C4V5A0E3W", "event_ts": "1572364286.379400",
                "ts": "1572364286.379400"}

        reply = message_event(event=data)
        assert reply, "Reply is empty"

        assert count_documents(self.db_collection, {'text': {'$exists': True}}) == 1

    def test_simple(self):
        message = "<@{}> question?".format(self.BOT_ID)
        self._test_success(message)

    def test_simple_russian(self):
        message = "<@{}> вопрос?".format(self.BOT_ID)
        self._test_success(message)

    def test_middle_question(self):
        message = "<@{}> question? word".format(self.BOT_ID)
        self._test_success(message)

    def test_middle_question_russian(self):
        message = "<@{}> вопрос? слово".format(self.BOT_ID)
        self._test_success(message)

    def test_multiple_question(self):
        message = "<@{}> question? question2? word".format(self.BOT_ID)
        self._test_success(message)

    def test_multiple_question2(self):
        message = "<@{}> вопрос? вопрос2? слово".format(self.BOT_ID)
        self._test_success(message)
