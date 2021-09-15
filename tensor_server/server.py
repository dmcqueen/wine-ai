#!/usr/bin/env python3

from sentence_transformers import SentenceTransformer
model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

from flask import Flask
from flask import request
from sentence_transformers import SentenceTransformer
import json

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def get_embedding():
    request_data = request.get_json()
    if request_data == None:
        return "can't get json"

    text = request_data['text']
    if text == None:
        return "can't get text"
    
    print(text)

    return json.dumps({ 
            "paraphrase-MiniLM-L6-v2" :  model.encode(text).tolist()
    })

if __name__ == '__main__':
    app.run(port=8088, host='0.0.0.0')
