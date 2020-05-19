import sys
from flask import Flask
from flask import request
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
import requests
import os
import sys, socket
import datetime
import threading
from datetime import datetime
import requests
import random
import string
import threading
from marshmallow import Schema, fields
import json
import time
import socket
import os
#import marshmallow_sqlalchemy

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'order.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)  # defining the sqlite db
#ma = Marshmallow(app)


# defining various urls
isLocal = False
catalog_url = 'localhost'

primary_path = 'primary_details.json' if isLocal else 'order/order_A/primary_details.json'


log_lock = threading.Lock()  #here is a lock to calculate time and performance

primary_details = None
#with open(primary_path) as f:

 # primary_details = json.load(f)


class PurchaseRequest(db.Model):

    id = db.Column(db.String(16), primary_key=True)  # unique id
    book_name = db.Column(db.String(16))  # name of the item
    item_number = db.Column(db.Integer, nullable=False)  # item number
    total_price = db.Column(db.Float, nullable=False)  # total price of the order
    remaining_stock = db.Column(db.Integer)  # remaining stock
    date_created = db.Column(db.DateTime, default=datetime.utcnow())  # date and time of the order


class PurchaseRequestSchema(Schema):

    id = fields.Str(dump_only=True)
    book_name = fields.Str(dump_only=True)
    item_number = fields.Int()
    total_price = fields.Float()
    remaining_stock = fields.Int()
    date_created = fields.DateTime()




@app.route('/buy/<int:args>', methods=['GET'])
def buy(args):

    # note the request start time
    request_start = datetime.now()
    #request_id = request.values['request_id']


    # form the query url and get the result
    port = 5001
    query_url = catalog_url + ':' + port + '/lookup/' + str(args)
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    request_success = False
    while not request_success:
        try:
            query_result = requests.get(url=query_url, data={}) #'request_id': request_id
            query_data = query_result.json()

            # if the item is in stock
            if query_data is not None and query_data['result']['quantity'] > 0:

                # form the query url and get the result
                update_url = catalog_url + ':' + port + '/bookupdate/' + str(args)
                update_result = requests.get(url=update_url, data={})
                update_data = update_result.json()

                # if the item is in stock
                if update_data['result'] == 0:
                    request_success = True
                    # create a unique order id
                    _id = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(16))

                    # create an order db object and add to orders db
                    purchase_request = PurchaseRequest(id=_id, book_name=query_data['result']['name'], item_number=args,
                                                       total_price=query_data['result']['cost'],
                                                       remaining_stock=update_data['remaining_stock'])
                    db.session.add(purchase_request)
                    db.session.commit()

                    # get the newly created order details
                    order_details = PurchaseRequest.query.filter_by(id=_id).first()
                    order_schema = PurchaseRequestSchema()
                    result = order_schema.dump(order_details)

                    # note the request end time and calculate the difference
                    request_end = datetime.now()
                    request_time = request_end - request_start

                    # acquire a lock on the file and write the time
                    log_lock.acquire()

                    print(request_time.microseconds / 1000)

                    log_lock.release()

                    # return the result
                    return {'result': 'Buy Successful', 'data': result, 'catalog_host/ip':update_data['catalog_host/ip'],
                              'order_host/ip': hostname+'/'+ip}

                # if the item is not in stock
                else:
                    # return failure
                    return {'result': 'Buy Failed!',
                            'data': {'book_name': query_data['result']['name'], 'item_number': args, 'remaining_stock': 0},
                            'catalog_host/ip': update_data['catalog_host/ip'],
                            'order_host/ip': hostname + '/' + ip
                            }
            # if the item is not in stock
            else:
                # return failure
                return {'result': 'Buy Failed!',
                        'data': {'book_name': query_data['result']['name'], 'item_number': args, 'remaining_stock': 0},
                        'catalog_host/ip': update_data['catalog_host/ip'],
                        'order_host/ip': hostname + '/' + ip
                        }

        except Exception:
            time.sleep(3)





@app.route('/', methods=['GET'])
def start():
    return "it's working!"
if __name__ == '__main__':

    app.run(host='localhost', port=5004)