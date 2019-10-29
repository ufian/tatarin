# Tatarin Slack Bot

Tatarin (formerly known as Udmurt; don't even ask) is a Slack bot for [Evergreen Podcast](https://podtema.com) Slack group.


## How to clone

```shell script

virtualenv --python=python3 --no-site-packages venv
source venv/bin/activate
git clone https://github.com/ufian/tatarin.git
cd tatarin
pip install -r requirements.txt

```

## How to configure

Configuration is based in file `slackbot_settings.py`. This is example of content

```python

# -*- coding: utf-8 -*-
API_TOKEN = "xoxb-0000000-xxxxx"

DB = {
    'db': 'database',
    'host': 'localhost',
    'port': 27017
}
```

## How to run unittests

You should execute `pytest`

```shell script
source venv/bin/activate
cd tatarin

pytest
```

example of output

```shell script
(venv) [ufian@mymac tatarin (master)]$ pytest
=========================================================================================================================================== test session starts ===========================================================================================================================================
platform darwin -- Python 3.7.4, pytest-5.2.2, py-1.8.0, pluggy-0.13.0
rootdir: /Users/ufian/tatarin/tatarin
collected 1 item

tests/test_questions.py .                                                                                                                                                                                                                                                                           [100%]

============================================================================================================================================ warnings summary =============================================================================================================================================
tests/test_questions.py::TestQuestions::test_simple
tests/test_questions.py::TestQuestions::test_simple
tests/test_questions.py::TestQuestions::test_simple
tests/test_questions.py::TestQuestions::test_simple
  /Users/ufian/tatarin/venv/lib/python3.7/site-packages/mongoengine/queryset/base.py:398: DeprecationWarning: count is deprecated. Use Collection.count_documents instead.
    count = self._cursor.count(with_limit_and_skip=with_limit_and_skip)

-- Docs: https://docs.pytest.org/en/latest/warnings.html
====================================================================================================================================== 1 passed, 4 warnings in 0.43s ======================================================================================================================================

```