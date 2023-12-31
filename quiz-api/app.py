from flask import Flask, request
from flask_cors import CORS
import hashlib
from jwt_utils import build_token, decode_token, JwtError
from db_request import *
from models import Question, Answer, ParticipationResult

app = Flask(__name__)
CORS(app)

@app.route('/')
def hello_world():
    x = 'world'
    return f"Hello, {x}"


@app.route("/rebuild-db", methods=['POST'])
def RebuildDb():
    code, err = create_db()
    if err != "":
        return {"ERROR": err}, code
    return "Ok", code


@app.route('/quiz-info', methods=['GET'])
def GetQuizInfo():
    response, code, err = get_quiz_info()
    if code != 200:
        return {"ERROR": err}, code
    size = response['size']

    scores = [participation.to_dict() for participation in response['participations']]
    return {"size": size, "scores": scores}, 200

@app.route("/login", methods=['POST'])
def Login():
    payload = request.get_json()
    tried_password = payload['password'].encode('UTF-8')
    hashed = hashlib.md5(tried_password).digest()
    if hashed == b'\xd8\x17\x06PG\x92\x93\xc1.\x02\x01\xe5\xfd\xf4_@':
         return {"token": build_token()}
    else:
         return 'Unauthorized', 401
    

    
@app.route("/questions", methods=['POST'])
def SaveQuestion():

    # REGARDE SI REQUETE A TOKEN DANS HEADER
    token = request.headers.get('Authorization')
    if token is None:
        return 'Unauthorized', 401
    token = token.split(' ')[1]
    try:
        decode_token(token)
    except JwtError as e:
        return {'error': str(e)}, 401  

    # TRANSFORME LA QUESTION RENSEIGNEE EN OBJET QUESTION
    data = request.get_json()
    question = Question.from_dict(data)

    # TRANSFORME LES REPONSES EN LISTES DOBJETS ANSWERS
    answers = [Answer.from_dict(answer) for answer in data['possibleAnswers']]

    # AJOUTE LA QUESTION RENSEIGNEE
    # AJOUTE LES REPONSES
    question_id, code, err = add_question(question)
    if code != 200:
        return {"ERROR": err}, code
    code, err = add_answers(answers, question_id)
    if code != 200:
        return {"ERROR": err}, code
    
    return {'id': question_id}, 200


@app.route("/questions/<int:question_id>", methods=['GET'])
def get_question_id(question_id:int):
     question_dict, code, err = get_question_by_id(question_id)
     if code != 200:
        return {"ERROR": err}, code
     else:
         return question_dict, code

@app.route("/questions", methods=['GET'])
def get_question_position():
    position = request.args.get('position')
    question_dict, code, err = get_question_by_position(position)
    if code != 200:
        return {"ERROR": err}, code
    else:
         return question_dict, code
    
@app.route("/questions/<int:question_id>", methods=['PUT'])
def update_question_id(question_id:int):
     
    # REGARDE SI REQUETE A TOKEN DANS HEADER
    token = request.headers.get('Authorization')
    if token is None:
        return 'Unauthorized', 401
    token = token.split(' ')[1]
    try:
        decode_token(token)
    except JwtError as e:
        return {'error': str(e)}, 401 
    
    data = request.get_json()
    question = Question.from_dict(data)
    answers = [Answer.from_dict(answer) for answer in data['possibleAnswers']]

    code, err = update_question_by_id(question_id, question, answers)
    if code != 204:
        return {"ERROR": err}, code
    return {"Message": err}, code

@app.route("/questions/<int:question_id>", methods=['DELETE'])
def delete_question_id(question_id:int):
    # REGARDE SI REQUETE A TOKEN DANS HEADER
    token = request.headers.get('Authorization')
    if token is None:
        return 'Unauthorized', 401
    token = token.split(' ')[1]
    try:
        decode_token(token)
    except JwtError as e:
        return {'error': str(e)}, 401 
    code, err = delete_question_by_id(question_id)
    if code != 204:
        return {"ERROR": err}, code
    return {"Message": err}, code
    
@app.route("/questions/all", methods=["DELETE"])
def delete_all():
    print("test")
    # REGARDE SI REQUETE A TOKEN DANS HEADER
    token = request.headers.get('Authorization')
    if token is None:
        return 'Unauthorized', 401
    token = token.split(' ')[1]
    try:
        decode_token(token)
    except JwtError as e:
        return {'error': str(e)}, 401

    except Exception as e:
        return {'bizarre error': str(e)}, 401
    code, err = delete_question_everything()
    if code != 204:
        return {"ERROR": err}, code
    return {"Message": err}, code
    

@app.route("/participations/all", methods=["DELETE"])
def delete_all_participations():
    token = request.headers.get('Authorization')
    if token is None:
        return 'Unauthorized', 401
    token = token.split(' ')[1]
    try:
        decode_token(token)
    except JwtError as e:
        return {'error': str(e)}, 401
    except Exception as e:
        return {'bizarre error': str(e)}, 401
    code, err = remove_all_participations()
    if code != 204:
        return {"ERROR": err}, code
    return {"Message": err}, code

@app.route("/participations", methods=["POST"])
def put_participations_in_db():
    data = request.get_json()

    player_name = data['playerName']
    answers = data['answers']

    participations, code, err = save_participations(player_name, answers)

    if code !=200:
        return {"ERROR": err}, code
    else:
        return {"answersSummaries":participations['answersSummaries'], "playerName":participations['playerName'], "score": participations['score']}, 200


@app.route("/questions/all", methods=['GET'])
def get_all_questions():
     
    # REGARDE SI REQUETE A TOKEN DANS HEADER
    token = request.headers.get('Authorization')
    if token is None:
        return 'Unauthorized', 401
    token = token.split(' ')[1]
    try:
        decode_token(token)
    except JwtError as e:
        return {'error': str(e)}, 401 
    
    all_questions, code, err = return_all_questions()
    if code !=200:
        return {"ERROR": err}, code
    else:
        return  all_questions, 200

     

if __name__ == '__main__':
    #app.run()
    app.run(debug=True)