from models import Question, Answer, ParticipationResult
import datetime
import sqlite3

import sqlite3

DB_CONNECTION = sqlite3.connect("test_rebuild.db", check_same_thread=False)
DB_CONNECTION.isolation_level = None

"""
Problème actuels :
- Ajout d'un objet déjà existant (question/réponse). SI on veut ajouter une question qui existe déjà comment gérer la chose ?
    - Gérer clés primaires, trouver existant, rediriger vers modification ?
- Faire TABLE pour réponses où intégrer les réponses comme champs des questions ?
    - Dans cas où table pour réponses -> ajouter réponses et questions seulement si pas erreur (pas faire l'un puis l'autre)
    - Dans cas où table pour réponses -> comment gérer leur unicité ?
- Cas où plusieurs réponses bonnes (part du principe qu'une bonne réponse par question ?)
"""


def check_question_exist(input_question: Question):
    CUR = DB_CONNECTION.cursor()

    err = ""
    try:
        CUR.execute("begin")
        CUR.execute(
            "select id from questions where position = ? and title = ? and text = ? and image = ?",
            (input_question.position, input_question.title, input_question.text, input_question.image))
        result = CUR.fetchone()
        DB_CONNECTION.commit()
        CUR.close()
    except Exception as e:
        err = str(e)
        DB_CONNECTION.rollback()
        CUR.close()
        return None, err
    
    if result is not None:
        # the question already exists, return its id
        return result[0], ""
    else:
        return None, ""


def add_question(input_question: Question):
    # AJOUT DE QUESTIONS (CAS OU ELLE EXITE DEJA => CHECK AVEC POSITION, TITRE, TEXTE ET IMAGE)
    id, err = check_question_exist(input_question)
    if err != "":
        return None, 500, err
    if id is not None:
        return id, 200, ""
    
    # start transaction
    CUR2 = DB_CONNECTION.cursor()
    CUR2.execute("begin")

    # INSERT LA QUESTION EN DB ET RECUPERE A LA VOLEE L'ID DE LA QUESTION
    try:
        CUR2.execute(
            "insert into questions (position, title, text, image) values (?, ?, ?, ?)",
            (input_question.position, input_question.title, input_question.text, input_question.image))
        # get the id of the last inserted row
        last_id = CUR2.lastrowid
        # send the request
        DB_CONNECTION.commit()
        CUR2.close()
        return last_id, 200, ""

    except sqlite3.IntegrityError:
        # Set the positions to a temporary negative value
        CUR2.execute("UPDATE questions SET position = -(position + 1) WHERE position >= ?", (input_question.position,))

        # Convert the positions back to positive, effectively shifting them down
        CUR2.execute("UPDATE questions SET position = -position WHERE position < 0")

        CUR2.execute(
            "insert into questions (position, title, text, image) values (?, ?, ?, ?)",
            (input_question.position, input_question.title, input_question.text, input_question.image))
        # get the id of the last inserted row
        last_id = CUR2.lastrowid
        # send the request
        DB_CONNECTION.commit()
        CUR2.close()
        return last_id, 200, ""

    except Exception as e:
        DB_CONNECTION.rollback()
        CUR2.close()
        return None, 500, str(e)


def check_answer_exist(CUR, input_answer: Answer, question_id: int):
    err = ""
    try :
        CUR.execute(
            "select id from answers where text = ? and is_correct = ? and id_question = ?",
            (input_answer.text, str(input_answer.is_correct), question_id))
        result = CUR.fetchone()
        DB_CONNECTION.commit()
    except Exception as e:
        DB_CONNECTION.rollback()
        CUR.close()
        err = str(e)
        return None, 500, err
    # SI EXISTE RENVOIE ID DE LA REPONSE EXISTANTE
    if result is not None:
        # the answer already exists, return its id
        return result[0], 200, ""
    else:
        return None, 404, ""


def add_answers(answers: list[Answer], question_id: int):
    # SI AJOUT DE REPONSE, AU MOINS UNE DOIT ETRE TRUE (VRAIE)
    correct_answers_count = sum(answer.is_correct for answer in answers)

    if correct_answers_count != 1:
        raise Exception("One answer must be correct (no more/less than 1)")

    CUR = DB_CONNECTION.cursor()
    CUR.execute("begin")

    try:
        count = 1
        for answer in answers:
            # SI REPONSE EXISTE DEJA, ON LA RECUPERE
            result, code, err = check_answer_exist(CUR, answer, question_id)
            if err != "":
                return code, err
            
            # SINON ON L'AJOUTE
            if result is None:
                # the answer does not exist, insert it

                CUR.execute(
                    "insert into answers (text, is_correct, id_question, order_added) values (?, ?, ?, ?)",
                    (answer.text, str(answer.is_correct), question_id, count))
                count += 1

        DB_CONNECTION.commit()
        CUR.close()

        return 200, ""

    except Exception as e:
        DB_CONNECTION.rollback()
        CUR.close()
        return 500, str(e)


def fetch_question(value, search_by_id=False):
    CUR = DB_CONNECTION.cursor()

    if search_by_id:
        CUR.execute("select * from questions where id = ?", (value,))
    else:
        CUR.execute("select * from questions where position = ?", (value,))
    result = CUR.fetchone()
    DB_CONNECTION.commit()
    CUR.close()
    if result is None:
        err = "No question found."
        return None, 404, err

    return Question(position=result[0], title=result[1], text=result[2], image=result[3], id=result[4]), 200, ""


def fetch_answers(id):
    CUR = DB_CONNECTION.cursor()
    CUR.execute("select text, is_correct from answers where id_question = ? order by order_added", (id,))
    answers = []
    for result in CUR.fetchall():
        correct = str_to_bool(result[1])
        answers.append(Answer(text=result[0], is_correct=correct).to_dict())
    DB_CONNECTION.commit()
    CUR.close()

    if len(answers)==0:
        err = "No answer found."
        return None, 404, err
    return answers, 200, ""


def get_question_by_id(id: int):
    CUR = DB_CONNECTION.cursor()
    CUR.execute("begin")

    try:

        # RECUPERE LA QUESTION PAR ID
        question, code, err = fetch_question(id, True)
        if err != "":
            return None, code, err

        # RECUPERE LES REPONSES ASSOCIEES
        answers, code, err = fetch_answers(question.id)
        if code != 200:
            return None, code, err

        question.possibleAnswers = answers
        DB_CONNECTION.commit()
        CUR.close()
        return question.to_dict(), 200, ""
    except Exception as e:
        DB_CONNECTION.rollback()
        CUR.close()
        return None, 500, str(e)


def get_question_by_position(position: int):
    CUR = DB_CONNECTION.cursor()
    CUR.execute("begin")

    try:
        question, code, err = fetch_question(position)
        if err != "":
            return {}, code, err

        # RECUPERE LES REPONSES ASSOCIEES
        CUR.execute("select * from answers where id_question = ? order by order_added", (question.id,))

        answers, code, err = fetch_answers(question.id)
        if err != "":
            return None, code, err

        DB_CONNECTION.commit()
        CUR.close()
        question.possibleAnswers = answers
        return question.to_dict(), 200, ""
    except Exception as e:
        DB_CONNECTION.rollback()
        CUR.close()
        return {}, 500,  str(e)


def str_to_bool(s):
    if s == 'True':
        return True
    elif s == 'False':
        return False
    else:
        raise ValueError


def update_question_by_id(id: int, input_question: Question, answers: list[Answer]):
    try:
        question, code, err =fetch_question(id, True)
        if err != "":
            return code, err
    except Exception as e:
        return 500, str(e)

    code, err = update_question_informations(input_question, id)
    if err != "":
        return code, err
    code, err = update_answers_informations(id, answers)
    if err != "":
        return code, err        
    return 204, ""



def update_question_informations(input_question: Question, id):
    CUR = DB_CONNECTION.cursor()
    CUR.execute("begin")
    try:
        CUR.execute(
            "UPDATE questions SET position = ?, title = ?, text = ?, image = ? WHERE id = ?",
            (input_question.position, input_question.title, input_question.text, input_question.image, id))
        DB_CONNECTION.commit()

        return 200, ""
    except sqlite3.IntegrityError:
        # Fetch the ID of the question with the new position
        old_question = CUR.execute("SELECT id, position FROM questions WHERE id = ?", (id,)).fetchone()
        _, old_question_position = old_question[0], old_question[1]

        # Temporarily set the position of the updating question to a non-existing value
        CUR.execute("UPDATE questions SET position = 0 WHERE id = ?", (id,))

        # Check if the new position is less than the old position
        if input_question.position < old_question_position:
            # Increment the position of all questions with a position greater than or equal to the new position and less than the old position
            CUR.execute("UPDATE questions SET position = -(position + 1) WHERE position >= ? AND position < ?",
                        (input_question.position, old_question_position))
        else:
            # Decrement the position of all questions with a position less than or equal to the new position and greater than the old position
            CUR.execute("UPDATE questions SET position = -(position - 1) WHERE position <= ? AND position > ?",
                        (input_question.position, old_question_position))

        # Update the position of the updating question with the new position
        CUR.execute("UPDATE questions SET position = ? WHERE id = ?", (input_question.position, id))

        CUR.execute("UPDATE questions SET title = ?, text = ?, image = ? WHERE id = ?", (input_question.title, input_question.text, input_question.image, id))

        CUR.execute("UPDATE questions SET position = -position WHERE position < 0")

        DB_CONNECTION.commit()
        CUR.close()
        return 200, ""
    except Exception as e:
        DB_CONNECTION.rollback()
        CUR.close()
        return 500, str(e)


def update_answers_informations(id: int, new_answers: list[Answer]):
    CUR = DB_CONNECTION.cursor()
    try:
        CUR.execute("DELETE FROM answers WHERE id_question = ?", (id,))
        DB_CONNECTION.commit()
        CUR.close()

        code, err = add_answers(new_answers, id)
        if err != "":
            return code, err
        return 200, ""
    except Exception as e:
        DB_CONNECTION.rollback()
        CUR.close()
        return 500, str(e)


def delete_question_by_id(id: int):
    CUR = DB_CONNECTION.cursor()
    try:
        question_to_delete, code, err = fetch_question(id, True)
        if err != "":
            return code, err
    except Exception as e:
        DB_CONNECTION.rollback()
        CUR.close()
        return 500, str(e)

    CUR.execute("begin")

    try:
        CUR.execute("DELETE FROM answers WHERE id_question = ?", (id,))
        CUR.execute("DELETE FROM questions WHERE id = ?", (id,))
        CUR.execute("UPDATE questions SET position = -(position - 1) WHERE position > ?",
                    (question_to_delete.position,))
        CUR.execute("UPDATE questions SET position = -position WHERE position < 0")

        DB_CONNECTION.commit()
        CUR.close()
        return 204, ""
    except Exception as e:
        DB_CONNECTION.rollback()
        CUR.close()
        return 500, str(e)


def delete_question_everything():
    CUR = DB_CONNECTION.cursor()
    CUR.execute("begin")

    try:
        CUR.execute("DELETE FROM answers")
        CUR.execute("DELETE FROM questions")
        DB_CONNECTION.commit()
        CUR.close()
        return 204, ""
    except Exception as e:
        DB_CONNECTION.rollback()
        CUR.close()
        return 500, str(e)

def get_number_of_questions():
    CUR = DB_CONNECTION.cursor()
    CUR.execute("begin")
    try:
        CUR.execute("SELECT COUNT(*) FROM questions")
        result = CUR.fetchone()[0]
        DB_CONNECTION.commit()
        CUR.close()
        return result, 200, ""
    except Exception as e:
        DB_CONNECTION.rollback()
        CUR.close()
        return None, 500, str(e)


def get_participations():
    CUR = DB_CONNECTION.cursor()
    CUR.execute("begin")

    try:
        CUR.execute("select playerName, score, date from participations order by score desc")
        rows = CUR.fetchall()
        participations = [ParticipationResult(row[0], row[1], row[2]) for row in rows]
        DB_CONNECTION.commit()
        CUR.close()
        return participations, 200, ""

    except Exception as e:
        DB_CONNECTION.rollback()
        CUR.close()
        return None, 500, str(e)

def get_quiz_info():
    try: 
        size, code, err = get_number_of_questions()
        if err != "":
            return None, code, err
        participations, code, err = get_participations()
        if err != "":
            return None, code, err
        return {"size":size, "participations":participations}, 200, ""
    except Exception as e:
        return None, 500, str(e)

def save_participations(player_name, answers):
    CUR = DB_CONNECTION.cursor()
    CUR.execute("begin")
    try:
        CUR.execute('SELECT order_added FROM answers INNER JOIN (SELECT id from questions ORDER BY position) as q ON q.id = answers.id_question WHERE answers.is_correct=="True"')
        result = CUR.fetchall()

        if check_answers_conformity(answers, result) == False:
            DB_CONNECTION.commit()
            CUR.close()
            return None, 400, "Answers do not match"
        
        answersSummaries = []
        final_score = 0
        for index in range(len(answers)):
            answers_i = answers[index]
            true_answers_i = result[index][0]

            print("type answers", type(answers_i))
            print("type true answers", type(true_answers_i))

            if answers_i == true_answers_i:
                final_score += 1
                answersSummaries.append({"correctAnswerPosition":true_answers_i, "wasCorrect":True})
            else:
                answersSummaries.append({"correctAnswerPosition":true_answers_i, "wasCorrect":False})


        current_date = datetime.datetime.now()
        CUR.execute("INSERT INTO participations (playerName, score, date) VALUES (?, ?, ?)", (player_name, final_score, current_date))
        DB_CONNECTION.commit()
        CUR.close()
        participationResult = {"playerName":player_name, "score":final_score, "answersSummaries":answersSummaries, "date":current_date}
        return participationResult, 200, ""

    except Exception as e:
        DB_CONNECTION.rollback()
        CUR.close()
        return None, 500, str(e)

def check_answers_conformity(answers, true_answers):
    if len(answers) != len(true_answers):
        return False
    return True
    

def remove_all_participations():
    CUR = DB_CONNECTION.cursor()
    CUR.execute("begin")

    try:
        CUR.execute("DELETE FROM participations")
        DB_CONNECTION.commit()
        CUR.close()
        return 204, "Everything deleted"
    except Exception as e:
        DB_CONNECTION.rollback()
        CUR.close()
        return 500, str(e)
    
def return_all_questions():
    CUR = DB_CONNECTION.cursor()
    CUR.execute("begin")

    try:
        CUR.execute("SELECT position, title, text, image, id FROM questions ORDER BY position")
        question_rows = CUR.fetchall()

        questions = []
        for question_row in question_rows:
            answers, code, err = fetch_answers(question_row[4])
            if err != "":
                return None, code, err

            question = Question(position=question_row[0], title=question_row[1], text=question_row[2], image=question_row[3], id=question_row[4], possibleAnswers=answers)
            print(question.possibleAnswers)
            print(question.to_dict())
            questions.append(question.to_dict())

        DB_CONNECTION.commit()
        CUR.close()

        return questions, 200, ""

    except Exception as e:
        DB_CONNECTION.rollback()
        CUR.close()
        return None, 500, str(e)
    

def create_db():

    db_name = 'test_rebuild'

    answers_table = """
    CREATE TABLE IF NOT EXISTS "answers" (
	"order_added"	INTEGER NOT NULL,
	"text"	TEXT NOT NULL,
	"id_question"	INTEGER NOT NULL,
	"id"	INTEGER NOT NULL,
	"is_correct"	TEXT NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	UNIQUE("text","id_question"))
    """

    participations_table = """
    CREATE TABLE IF NOT EXISTS "participations" (
	"playerName"	TEXT,
	"score"	INTEGER,
	"id"	INTEGER NOT NULL,
	"date"	TEXT,
	PRIMARY KEY("id" AUTOINCREMENT))
    """

    questions_table = """
    CREATE TABLE IF NOT EXISTS "questions" (
	"position"	INTEGER NOT NULL UNIQUE,
	"title"	TEXT,
	"text"	TEXT NOT NULL UNIQUE,
	"image"	TEXT,
	"id"	INTEGER UNIQUE,
	PRIMARY KEY("id" AUTOINCREMENT))
    """
    try:
        conn = sqlite3.connect(f'{db_name}.db')
        c = conn.cursor()

        c.execute(answers_table)
        c.execute(participations_table)
        c.execute(questions_table)

        conn.commit()
        conn.close()

        return 200, ""
    except Exception as e:
        return 500, str(e)

