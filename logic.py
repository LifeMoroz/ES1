from models import Question, Answer, Actor, Link


def print_question(question: Question) -> Answer:
    print(question.text)
    result_dict = {}
    for i, a in enumerate(question.get_answers(), 1):
        print("{}) {}".format(i, a.text))
        result_dict[i] = a

    while 1:
        try:
            s = int(input('Ваш ответ: '))
            break
        except ValueError:
            pass
    return result_dict[s]


def ask(question, actor):
    answer = print_question(question)
    actor.add_param(answer.get_params())
    return answer


def get_next_question(answer, actor) -> Question:
    links = Link.find(answer_id=answer.id)
    max_ = (-10000, None)
    for link in links:
        result = {}
        exec("result[0] = " + link.expr, {"result": result}, actor.get_params())
        new = result[0]
        if max_[0] < new:
            max_ = (new, link)
    if max_[1] and max_[1].question_id is not None:
        return Question.find(id=max_[1].question_id)[0]
    return None


def main():
    actor = Actor.find(id=0)[0]
    new_question = Question.find(is_start=1)[0]
    while new_question:
        answer = ask(new_question, actor)
        new_question = get_next_question(answer, actor)

if __name__ == "__main__":
    main()
