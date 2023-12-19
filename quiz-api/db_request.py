from models import Question, Answer
import datetime
import sqlite3

import sqlite3

DB_CONNECTION = sqlite3.connect("maBDD.db", check_same_thread=False)
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
    CUR.execute("begin")
    CUR.execute(
        "select id from questions where position = ? and title = ? and text = ? and image = ?",
        (input_question.position, input_question.title, input_question.text, input_question.image))
    result = CUR.fetchone()
    DB_CONNECTION.commit()
    # SI EXISTE RENVOIE ID DE LA QUESTION EXISTANTE
    CUR.close()
    if result is not None:
        # the question already exists, return its id
        return result[0], 200
    else:
        return None, 404


def add_question(input_question: Question):
    # AJOUT DE QUESTIONS (CAS OU ELLE EXITE DEJA => CHECK AVEC POSITION, TITRE, TEXTE ET IMAGE)
    id, code = check_question_exist(input_question)
    if id is not None:
        return id, code
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
        return last_id, 200

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
        return last_id, 200

    except Exception as e:
        DB_CONNECTION.rollback()
        CUR2.close()
        raise Exception(e)


def check_answer_exist(CUR, input_answer: Answer, question_id: int):
    CUR.execute(
        "select id from answers where text = ? and is_correct = ? and id_question = ?",
        (input_answer.text, str(input_answer.is_correct), question_id))
    result = CUR.fetchone()
    DB_CONNECTION.commit()
    # SI EXISTE RENVOIE ID DE LA REPONSE EXISTANTE
    if result is not None:
        # the answer already exists, return its id
        return result[0], 200
    else:
        return None, 404


def add_answers(answers: list[Answer], question_id: int):
    # SI AJOUT DE REPONSE, AU MOINS UNE DOIT ETRE TRUE (VRAIE)
    correct_answers_count = sum(answer.is_correct for answer in answers)

    if correct_answers_count != 1:
        raise Exception("One answer must be correct (no more/less than 1)")

    CUR = DB_CONNECTION.cursor()
    CUR.execute("begin")

    try:
        count = 0
        for answer in answers:
            # SI REPONSE EXISTE DEJA, ON LA RECUPERE
            result, code = check_answer_exist(CUR, answer, question_id)
            # SINON ON L'AJOUTE
            if result is None:
                # the answer does not exist, insert it

                CUR.execute(
                    "insert into answers (text, is_correct, id_question, order_added) values (?, ?, ?, ?)",
                    (answer.text, str(answer.is_correct), question_id, count))
                count += 1

        DB_CONNECTION.commit()
        CUR.close()

        return "Answers added", 200

    except Exception as e:

        DB_CONNECTION.rollback()
        CUR.close()
        raise Exception(e)


def fetch_question(value, search_by_id=False):
    CUR = DB_CONNECTION.cursor()
    if search_by_id:
        CUR.execute("select * from questions where id = ?", (value,))
    else:
        CUR.execute("select * from questions where position = ?", (value,))
    result = CUR.fetchone()
    DB_CONNECTION.commit()
    CUR.close()
    if result is None or len(result) < 5:
        raise Exception("No question found or not enough fields in the question record.")

    return Question(position=result[0], title=result[1], text=result[2], image=result[3], id=result[4])


def fetch_answers(id):
    CUR = DB_CONNECTION.cursor()
    CUR.execute("select text, is_correct from answers where id_question = ? order by order_added", (id,))
    answers = []
    for result in CUR.fetchall():
        correct = str_to_bool(result[1])
        answers.append(Answer(text=result[0], is_correct=correct).to_dict())
    DB_CONNECTION.commit()
    CUR.close()
    return answers


def get_question_by_id(id: int):
    CUR = DB_CONNECTION.cursor()
    CUR.execute("begin")

    try:

        # RECUPERE LA QUESTION PAR ID
        question = fetch_question(id, True)

        # RECUPERE LES REPONSES ASSOCIEES
        answers = fetch_answers(question.id)

        question.possibleAnswers = answers
        DB_CONNECTION.commit()
        CUR.close()
        return question.to_dict(), 200
    except Exception as e:
        DB_CONNECTION.rollback()
        CUR.close()
        return {'error': str(e)}, 404


def get_question_by_position(position: int):
    CUR = DB_CONNECTION.cursor()
    CUR.execute("begin")

    try:
        question = fetch_question(position)

        # RECUPERE LES REPONSES ASSOCIEES
        CUR.execute("select * from answers where id_question = ? order by order_added", (question.id,))

        answers = fetch_answers(question.id)

        DB_CONNECTION.commit()
        CUR.close()
        question.possibleAnswers = answers
        return question.to_dict(), 200
    except Exception as e:
        DB_CONNECTION.rollback()
        CUR.close()
        return "rollback", 404


def str_to_bool(s):
    if s == 'True':
        return True
    elif s == 'False':
        return False
    else:
        raise ValueError


def update_question_by_id(id: int, input_question: Question, answers: list[Answer]):
    try:
        fetch_question(id, True)
    except Exception as e:
        return {'error': str(e)}, 404

    try:
        update_question_informations(input_question, id)
        update_answers_informations(id, answers)
        return "Question updated", 204
    except Exception as e:
        raise (e)


def update_question_informations(input_question: Question, id):
    CUR = DB_CONNECTION.cursor()
    CUR.execute("begin")
    try:
        CUR.execute(
            "UPDATE questions SET position = ?, title = ?, text = ?, image = ? WHERE id = ?",
            (input_question.position, input_question.title, input_question.text, input_question.image, id))
        DB_CONNECTION.commit()
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
        CUR.execute("UPDATE questions SET position = -position WHERE position < 0")

        DB_CONNECTION.commit()
        CUR.close()
    except Exception as e:
        DB_CONNECTION.rollback()
        CUR.close()
        raise (e)


def update_answers_informations(id: int, new_answers: list[Answer]):
    CUR = DB_CONNECTION.cursor()
    try:
        CUR.execute("DELETE FROM answers WHERE id_question = ?", (id,))
        DB_CONNECTION.commit()
        CUR.close()

        add_answers(new_answers, id)
    except Exception as e:
        DB_CONNECTION.rollback()
        CUR.close()
        raise (e)


def delete_question_by_id(id: int):
    CUR = DB_CONNECTION.cursor()
    try:
        question_to_delete = fetch_question(id, True)
    except Exception as e:
        DB_CONNECTION.rollback()
        CUR.close()
        return {'error': str(e)}, 404

    CUR.execute("begin")

    try:
        CUR.execute("DELETE FROM answers WHERE id_question = ?", (id,))
        CUR.execute("DELETE FROM questions WHERE id = ?", (id,))
        CUR.execute("UPDATE questions SET position = -(position - 1) WHERE position > ?",
                    (question_to_delete.position,))
        CUR.execute("UPDATE questions SET position = -position WHERE position < 0")

        DB_CONNECTION.commit()
        CUR.close()
        return "Question deleted", 204
    except Exception as e:
        DB_CONNECTION.rollback()
        CUR.close()
        raise (e)


def delete_question_everything():
    CUR = DB_CONNECTION.cursor()
    CUR.execute("begin")

    try:
        CUR.execute("DELETE FROM answers")
        CUR.execute("DELETE FROM questions")
        DB_CONNECTION.commit()
        CUR.close()
        return "Everything deleted", 204
    except Exception as e:
        DB_CONNECTION.rollback()
        CUR.close()
        raise (e)
