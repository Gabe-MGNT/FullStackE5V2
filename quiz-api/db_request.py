from models import Question, Answer
from database import get_cursor
import datetime
import sqlite3

"""
Problème actuels :
- Ajout d'un objet déjà existant (question/réponse). SI on veut ajouter une question qui existe déjà comment gérer la chose ?
    - Gérer clés primaires, trouver existant, rediriger vers modification ?
- Faire TABLE pour réponses où intégrer les réponses comme champs des questions ?
    - Dans cas où table pour réponses -> ajouter réponses et questions seulement si pas erreur (pas faire l'un puis l'autre)
    - Dans cas où table pour réponses -> comment gérer leur unicité ?
- Cas où plusieurs réponses bonnes (part du principe qu'une bonne réponse par question ?)
"""

def check_question_exist(CUR, input_question:Question):
    CUR.execute(
        "select id from questions where position = ? and title = ? and text = ? and image = ?",
        (input_question.position, input_question.title, input_question.text, input_question.image))
    result = CUR.fetchone()
    # SI EXISTE RENVOIE ID DE LA QUESTION EXISTANTE
    if result is not None:
        # the question already exists, return its id
        return result[0], 200
    else:
        return None, 404


def add_question(input_question: Question):
    CUR = get_cursor()

    # AJOUT DE QUESTIONS (CAS OU ELLE EXITE DEJA => CHECK AVEC POSITION, TITRE, TEXTE ET IMAGE)
    id, code = check_question_exist(CUR, input_question)
    if id is not None:
        return id, code

    # start transaction
    CUR.execute("begin")

    # INSERT LA QUESTION EN DB ET RECUPERE A LA VOLEE L'ID DE LA QUESTION
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
        raise Exception(e)



def check_answer_exist(CUR, input_answer:Answer, question_id:int):  
    CUR.execute(
        "select id from answers where text = ? and isCorrect = ? and id_question = ?",
        (input_answer.text, str(input_answer.isCorrect), question_id))
    result = CUR.fetchone()
    # SI EXISTE RENVOIE ID DE LA REPONSE EXISTANTE
    if result is not None:
        # the answer already exists, return its id
        return result[0], 200
    else:
        return None, 404    


def add_answers(answers:list[Answer], question_id:int):
    CUR = get_cursor()

    # SI AJOUT DE REPONSE, AU MOINS UNE DOIT ETRE TRUE (VRAIE)
    correct_answer_exists = any(answer.isCorrect for answer in answers)

    if not correct_answer_exists:
        raise Exception("At least one answer must be correct")

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
                    "insert into answers (text, isCorrect, id_question, order_added) values (?, ?, ?, ?)",
                    (answer.text, str(answer.isCorrect), question_id, count))
                count +=1

        # send the request
        CUR.execute("commit")
        return "Answers added", 200

    except Exception as e:
        CUR.execute("rollback")
        print(e)
        raise Exception("rollback")
    

def fetch_question(CUR, value, search_by_id=False):
    if search_by_id:
        CUR.execute("select * from questions where id = ?", (value,))
    else:
        CUR.execute("select * from questions where position = ?", (value,))
    result = CUR.fetchone()
    if result is None or len(result) < 5:
        raise Exception("No question found or not enough fields in the question record.")
    return Question(position=result[0], title=result[1], text=result[2], image=result[3], id=result[4])


def fetch_answers(CUR, id):
    CUR.execute("select text, isCorrect from answers where id_question = ? order by order_added", (id,))
    answers = []
    for result in CUR.fetchall():
        correct = str_to_bool(result[1])
        answers.append(Answer(text=result[0], isCorrect=correct).to_dict())
    return answers


def get_question_by_id(id:int):
    CUR = get_cursor()
    CUR.execute("begin")

    try:

        # RECUPERE LA QUESTION PAR ID
        question = fetch_question(CUR, id, True)

        # RECUPERE LES REPONSES ASSOCIEES
        answers = fetch_answers(CUR, question.id)

        CUR.execute("commit")

        question.possibleAnswers = answers
        return question.to_dict(), 200
    except Exception as e:
        CUR.execute("rollback")
        return {'error': str(e)}, 404
    
def get_question_by_position(position:int):
    CUR = get_cursor()
    CUR.execute("begin")

    try:
        question = fetch_question(CUR, position)

        # RECUPERE LES REPONSES ASSOCIEES
        CUR.execute("select * from answers where id_question = ? order by order_added", (question.id,))
        
        answers = fetch_answers(CUR, question.id)

        CUR.execute("commit")

        question.possibleAnswers = answers
        return question.to_dict(), 200
    except Exception as e:
        CUR.execute("rollback")
        print(e)
        return "rollback", 404
    

def str_to_bool(s):
    if s == 'True':
        return True
    elif s == 'False':
        return False
    else:
        raise ValueError
    

def update_question_by_id(id:int, input_question: Question, answers:list[Answer]):

    CUR = get_cursor()
    try:
        fetch_question(CUR, id, True)
    except Exception as e:
        return {'error': str(e)}, 404
    
    CUR.execute("begin")

    try:
        update_question_informations(CUR, input_question, id)
        update_answers_informations(CUR, id, answers)
        return "Question updated", 204
    except Exception as e:
        raise(e)
    
def update_question_informations(CUR, input_question: Question, id):
    try:
        CUR.execute(
                "UPDATE questions SET position = ?, title = ?, text = ?, image = ? WHERE id = ?",
                (input_question.position, input_question.title, input_question.text, input_question.image, id))
        CUR.execute("commit")
    except sqlite3.IntegrityError:
        # Fetch the ID of the question with the new position
        old_question = CUR.execute("SELECT id, position FROM questions WHERE id = ?", (id,)).fetchone()
        _, old_question_position = old_question[0], old_question[1] 

        # Temporarily set the position of the updating question to a non-existing value
        CUR.execute("UPDATE questions SET position = -1 WHERE id = ?", (id,))

        other_question_id = CUR.execute("SELECT id FROM questions WHERE position = ?", (input_question.position,)).fetchone()[0]
        # Update the position of the fetched question with the old position of the updating question
        CUR.execute("UPDATE questions SET position = ? WHERE id = ?", (old_question_position, other_question_id))

        # Update the position of the updating question with the new position
        CUR.execute("UPDATE questions SET position = ? WHERE id = ?", (input_question.position, id))

        CUR.execute("commit")
    except Exception as e:
        CUR.execute("rollback")
        raise(e)
    
def update_answers_informations(CUR, id:int, new_answers:list[Answer]):
    try:
        CUR.execute("DELETE FROM answers WHERE id_question = ?", (id,))
        print(new_answers)
        add_answers(new_answers, id)
    except Exception as e:
        raise(e)


def delete_question_by_id(id:int):
    CUR = get_cursor()
    try:
        fetch_question(CUR, id, True)
    except Exception as e:
        return {'error': str(e)}, 404
    
    CUR.execute("begin")

    try:
        CUR.execute("DELETE FROM answers WHERE id_question = ?", (id,))
        CUR.execute("DELETE FROM questions WHERE id = ?", (id,))
        CUR.execute("commit")
        return "Question deleted", 204
    except Exception as e:
        CUR.execute("rollback")
        raise(e)
    
def delete_question_everything():
    CUR = get_cursor()
    CUR.execute("begin")

    try:
        CUR.execute("DELETE FROM answers")
        CUR.execute("DELETE FROM questions")
        CUR.execute("commit")
        return "Everything deleted", 204
    except Exception as e:
        CUR.execute("rollback")
        raise(e)