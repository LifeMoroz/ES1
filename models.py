import json
from db import BaseActiveRecord, Field


class Question(BaseActiveRecord):
    table_name = 'question'

    text = Field()
    is_start = Field()

    def get_answers(self) -> list:
        return Answer.find(question_id=self.id)


class Answer(BaseActiveRecord):
    table_name = 'answer'

    question_id = Field()
    text = Field()
    add_params = Field()

    def get_params(self):
        return json.loads(self.add_params)


class Link(BaseActiveRecord):
    table_name = 'link'

    answer_id = Field()
    question_id = Field()
    expr = Field()


class Actor(BaseActiveRecord):
    table_name = 'actor'

    data = Field()

    def get_params(self):
        return json.loads(self.data)

    def set_params(self, params):
        self.data = json.dumps(params)

    def add_param(self, ddict):
        params = self.get_params()
        params.update(ddict)
        self.set_params(params)
