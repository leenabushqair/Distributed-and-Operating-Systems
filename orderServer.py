from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import requests
import random
import string
import threading
from flask_marshmallow import Marshmallow
import os




cat_url = 'http://192.168.1.64:51814'
app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'order.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Init db
db = SQLAlchemy(app)
# Init ma
ma = Marshmallow(app)
class Book(db.Model):
    id = db.Column(db.String(16), primary_key=True)  # unique id
    itemnums = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float)
    remaining_stock = db.Column(db.Integer)  # remaining stock
    book_name = db.Column(db.String(100), unique=True)

    def __init__(self, id, itemnums, price, remaining_stock, book_name):
        self.id = id
        self.itemnums = itemnums
        self.price = price
        self.remaining_stock = remaining_stock
        self.book_name = book_name

#Schema
class bookschema(ma.Schema):
    class Meta:
        fields = ('id', 'itemnums', 'price', 'remaining_stock', 'book_name')


book_schema = bookschema()
books_schema = bookschema( many=True)

#buy-request

@app.route('/buy/<int:args>')
def buy(args):


    request_id = request.values['request_id']

    # form the query url and get the result
    query_url = cat_url + '/query_by_item/' + str(args)
    query_result = requests.get(url=query_url, data={'request_id': request_id})
    query_data = query_result.json()

    # if the item is in stock
    if query_data is not None and query_data['result']['quantity'] > 0:

        # form the query url and get the result
        update_url = cat_url + '/update/' + str(args)
        update_result = requests.get(url=update_url, data={'request_id': request_id})
        update_data = update_result.json()

        # if the item is in stock
        if update_data['result'] == 0:
            # create a unique order id
            _id = ''.join(
                random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(16))

            # create an order db object and add to orders db
            req = Book(id=_id, itemnums= args,
                                               price=query_data['result']['cost'],
                                               remaining_stock=update_data['remaining_stock'],book_name=query_data['result']['name'])
            db.session.add(req)
            db.session.commit()

            # get the newly created order details
            order_details = Book.query.filter_by(id=_id).first()
            order_schema = bookschema()
            result = order_schema.dump(order_details)
            # return the result
            return {'Buy Successful': result}

        # if the item is not in stock
        else:
            # return failure
            return {'Buy Failed!'}

    # if the item is not in stock
    else:
        # return failure


        return {'Buy Failed!'}

@app.route('/', methods=['GET'])
def start():
  return "it's working!"

if __name__ == '__main__':
    app.run(host='192.168.1.64', port=51817, debug=True)