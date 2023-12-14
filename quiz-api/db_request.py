from models import Question, Answer
from database import get_cursor
import datetime


"""
Problème actuels :
- Ajout d'un objet déjà existant (question/réponse). SI on veut ajouter une question qui existe déjà comment gérer la chose ?
    - Gérer clés primaires, trouver existant, rediriger vers modification ?
- Faire TABLE pour réponses où intégrer les réponses comme champs des questions ?
    - Dans cas où table pour réponses -> ajouter réponses et questions seulement si pas erreur (pas faire l'un puis l'autre)
    - Dans cas où table pour réponses -> comment gérer leur unicité ?
- Cas où plusieurs réponses bonnes (part du principe qu'une bonne réponse par question ?)
"""

def add_question(input_question: Question):
    CUR = get_cursor()

    # AJOUT DE QUESTIONS (CAS OU ELLE EXITE DEJA => CHECK AVEC POSITION, TITRE, TEXTE ET IMAGE)
    CUR.execute(
        "select id from questions where position = ? and title = ? and text = ? and image = ?",
        (input_question.position, input_question.title, input_question.text, input_question.image))
    result = CUR.fetchone()

    # SI EXISTE RENVOIE ID DE LA QUESTION EXISTANTE
    if result is not None:
        # the question already exists, return its id
        return result[0], 200

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
        raise Exception("rollback  on adding question")



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
            CUR.execute(
                "select text from answers where text = ? and isCorrect = ? and position_question = ?",
                (answer.text, str(answer.isCorrect), question_id))
            result = CUR.fetchone()
            # SINON ON L'AJOUTE
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

        # RECUPERE LA QUESTION PAR ID
        CUR.execute("select * from questions where id = ?", (id,))
        result = CUR.fetchone()
        if result is None or len(result) < 5:
            raise Exception("No question found or not enough fields in the question record.")
        question = Question(position=result[0], title=result[1], text=result[2], image=result[3], id=result[4])

        # RECUPERE LES REPONSES ASSOCIEES
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
    CUR.execute("begin")

    try:
        CUR.execute("select * from questions where position = ?", (position,))
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