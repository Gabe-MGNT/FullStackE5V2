from models import Question
import sqlite3



def add_question(input_question: Question):
    
    # create a connection
    db_connection = sqlite3.connect("quizdb.db")

    # set the sqlite connection in "manual transaction mode"
    # (by default, all execute calls are performed in their own transactions, not what we want)
    db_connection.isolation_level = None

    CUR = db_connection.cursor()

    # start transaction
    CUR.execute("begin")

    # save the question to db
    try:
        insertion_result = CUR.execute(
            "insert into questions (position, title, text, image) values (?, ?, ?, ?)",
            (input_question.position, input_question.title, input_question.text, input_question.image))
        # send the request
        last_id = CUR.lastrowid
        CUR.execute("commit")
        return last_id, 200

    except Exception as e:
        CUR.execute("rollback")
        raise Exception("rollback")



def get_question(id:int):
    db_connection = sqlite3.connect("quizdb.db")
    db_connection.isolation_level = None
    CUR = db_connection.cursor()
    try:
        CUR.execute("select * from questions where id = ?", (id,))
        result = CUR.fetchone()
        return Question(result[1], result[2], result[3], result[4]).to_dict(), 200
    except Exception as e:
        CUR.execute("rollback")
        return "rollback", 500