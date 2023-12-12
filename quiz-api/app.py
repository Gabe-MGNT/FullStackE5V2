from flask import Flask, request
from flask_cors import CORS
import hashlib
from jwt_utils import build_token, decode_token, JwtError
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

if __name__ == '__main__':
    app.run()