from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import requests
import random
import string
import threading
from flask_marshmallow import Marshmallow
import os

app = Flask(__name__)
cat_url = 'http://192.168.1.64:51814'
order_url = 'http://192.168.1.64:51817'


# Get Single book by its topic
@app.route('/book/<args>', methods=['GET'])
def get_book(args):
    request_id = request.values['request_id']
    # form the query url and get the result
    query_url = cat_url + '/query_by_subject/' + str(args)
    query_result = requests.get(url=query_url, data={'request_id': request_id})

# return the results
    return query_result.json()

@app.route('/buy/<args>', methods=["GET"])
def buy(args):

    # note the starting time of the request
    request_start = datetime.datetime.now()
    request_id = request.values['request_id']

    # form the query url and get the result
    query_url = order_url + '/buy/' + str(args)
    query_result = requests.get(url=query_url, data={'request_id': request_id})

    # return the results
    return query_result.json()

@app.route('/', methods=['GET'])
def start():
  return "it's working!"

if __name__ == '__main__':
    app.run(host='192.168.1.64', port=51446, debug=True)