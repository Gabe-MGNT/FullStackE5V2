from flask import Flask, request
from flask_cors import CORS
import hashlib
from jwt_utils import build_token, decode_token, JwtError
from db_request import add_question, get_question_by_id, get_question_by_position, add_answers
from models import Question, Answer

app = Flask(__name__)
CORS(app)

@app.route('/')
def hello_world():
    x = 'world'
    return f"Hello, {x}"

@app.route('/quiz-info', methods=['GET'])
def GetQuizInfo():
	return {"size": 0, "scores": []}, 200

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
    token = request.headers.get('Authorization')

    if token is None:
        return 'Unauthorized', 401
    token = token.split(' ')[1]

    data = request.get_json()

    question = Question.from_dict(data)
    question_id, status = add_question(question)

    if status != 200:
        return {'error': 'Failed to add question'}, status

    answers = [Answer.from_dict(answer) for answer in data['possibleAnswers']]

    try:
        add_answers(answers, question_id)
    except Exception as e:
        return {'error': str(e)}, 400

    return {'id': question_id}, 200


@app.route("/questions/<int:question_id>", methods=['GET'])
def get_question(question_id:int):
     response, code = get_question_by_id(question_id)
     if code ==200:
        return response


     

     

if __name__ == '__main__':
    app.run()