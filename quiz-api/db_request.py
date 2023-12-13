from models import Question, Answer
from database import get_cursor
import datetime

def add_question(input_question: Question):
    CUR = get_cursor()

    # check if the question already exists
    CUR.execute(
        "select id from questions where position = ? and title = ? and text = ? and image = ?",
        (input_question.position, input_question.title, input_question.text, input_question.image))
    result = CUR.fetchone()

    if result is not None:
        # the question already exists, return its id
        return result[0], 200

    # start transaction
    CUR.execute("begin")

    # save the question to db
    try:
        CUR.execute(
            "insert into questions (position, title, text, image) values (?, ?, ?, ?)",
            (input_question.position, input_question.title, input_question.text, input_question.image))
        # get the id of the last inserted row
        last_id = CUR.lastrowid
        # send the request
        CUR.execute("commit")
        return last_id, 200

    except Exception as e:
        CUR.execute("rollback")
        raise Exception("rollback  on adding question")
    


def add_answers(answers:list[Answer], question_id:int):
    CUR = get_cursor()

    correct_answer_exists = any(answer.isCorrect for answer in answers)

    if not correct_answer_exists:
        raise Exception("At least one answer must be correct")

    # start transaction
    CUR.execute("begin")

    try:
        count = 0
        for answer in answers:
            # check if the answer already exists
            CUR.execute(
                "select text from answers where text = ? and isCorrect = ? and position_question = ?",
                (answer.text, str(answer.isCorrect), question_id))
            result = CUR.fetchone()

            if result is None:
                # the answer does not exist, insert it
                CUR.execute(
                    "insert into answers (text, isCorrect, position_question, timestamp) values (?, ?, ?, ?)",
                    (answer.text, str(answer.isCorrect), question_id, count))
                
                count +=1

        # send the request
        CUR.execute("commit")
        return "Answers added", 200

    except Exception as e:
        CUR.execute("rollback")
        print(e)
        raise Exception("rollback")

def get_question_by_id(id:int):
    CUR = get_cursor()
    CUR.execute("begin")

    try:
        CUR.execute("select * from questions where id = ?", (id,))
        result = CUR.fetchone()
        if result is None or len(result) < 5:
            raise Exception("No question found or not enough fields in the question record.")
        question = Question(position=result[0], title=result[1], text=result[2], image=result[3], id=result[4])

        CUR.execute("select * from answers where position_question = ? order by timestamp", (question.position,))
        answers = []
        for result in CUR.fetchall():
            print(result)
            if len(result) < 3:
                raise Exception("Not enough fields in the answer record.")
            
            s = result[2]
            correct = None
            if s == 'True':
                correct = True
            elif s == 'False':
                correct =  False
            else:
                raise ValueError
            
            answers.append(Answer(text=result[1], isCorrect=correct).to_dict())

        CUR.execute("commit")

        question.possibleAnswers = answers
        return question.to_dict(), 200
    except Exception as e:
        print(e)
        return "rollback", 500
    
def get_question_by_position(position:int):
    CUR = get_cursor()
    try:
        CUR.execute("select * from questions where position = ?", (position,))
        result = CUR.fetchone()
        question = Question(result[1], result[2], result[3], result[4]).to_dict()

        CUR.execute("select * from answers where question_id = ?", (result[0],))
        answers = [Answer(result[1], result[2], result[3]).to_dict() for result in CUR.fetchall()]

        return {'question': question, 'answers': answers}, 200
    except Exception as e:
        CUR.execute("rollback")
        return "rollback", 500