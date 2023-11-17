from flask import Flask, request
from miscellaneous import prettify_json
import json

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    file = open('github_update.txt', 'w')
    file.write(prettify_json(json.dumps(request.json)))
    file.close()
    return 'Success', 200

@app.route('/get', methods=['GET'])
def get():
    return 'Success', 500


if __name__ == '__main__':
    app.run(debug=True, port=4040)
