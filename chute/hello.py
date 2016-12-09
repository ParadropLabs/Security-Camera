from flask import Flask
from flask import request
app = Flask(__name__)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return ('get message')
    else:
        return ("error")

@app.route('/')
def hello_world():
    return 'Hello, World!'

app.run(port = 5001)

#if(__name__ == "__main__"):
#    print("In Main")
