from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields
from flask_marshmallow import Marshmallow
import requests
import os
import sys, socket
import datetime
import threading


app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Init db
db = SQLAlchemy(app)
# Init ma
ma = Marshmallow(app)
replica_host ='localhost'
catport = 5001
replica_port = 5002
write_lock = threading.Lock() #lock for updating the db
# book class
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    quantity = db.Column(db.Integer, nullable=False)
    cost = db.Column(db.Integer)
    topic = db.Column(db.String(100))

"""""
    def __init__(self,name, quantity, cost, topic ):
        self.quantity = quantity
        self.cost = cost
        self.topic = topic
        self.name = name
"""

# Schema
class bookschema(Schema):

    id = fields.Int(dump_only=True)
    name = fields.Str()
    quantity = fields.Int()
    cost = fields.Integer()
    topic = fields.Str()


book_schema = bookschema()
books_schema = bookschema(many=True)





# Get All books
@app.route('/books', methods=['GET'])
def get_books():
    all_books = Book.query.all()
    result = books_schema.dump(all_books)
    return jsonify(result)


# Get Single book by its topic
# query_by_subject
@app.route('/search/<args>', methods=['GET'])
def search(args):
    # to calculate the request time for the report
    write_lock.acquire()
    request_start = datetime.datetime.now()

    catalogs_schema = bookschema(many=True)
    books = Book.query.with_entities(Book.name, Book.id).filter_by(topic=args.lower()).all()


    # dump the result in a JSON
    result = catalogs_schema.dump(books)
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    result.append({'catalog_host/ip':  hostname + '/' + ip})
    # note the request end time and calculate the difference
    request_end = datetime.datetime.now()
    request_time = request_end - request_start
    # return the result
    print(request_time.microseconds / 1000)
    return {'results': result}

#search by id
@app.route('/lookup/<int:args>', methods=["GET"])
def lookup(args):

    # note the request start time for the report calculations
    request_start = datetime.datetime.now()
    #request_id = request.values['request_id']

    # query the catalog db
    books_schema = bookschema()
    books = Book.query.with_entities(Book.name, Book.quantity, Book.cost).filter_by(id=args).first()

    # dump the result in a JSON
    result = books_schema.dump(books)
    replica = 'catalogServer' if catport == '5001' else 'catalogReplication'
    result['replica'] = replica
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    result['catalog_host/ip'] = hostname + '/' + ip
    # note the request end time and calculate the difference
    request_end = datetime.datetime.now()
    request_time = request_end - request_start

    # acquire a lock on the file and write the time taken


    print(request_time.microseconds / 1000)


    # return the result

    return {'result': result}


# Update a book by its item number
#adding some changes here to make sure that there is consistancy with the replicated server
@app.route('/update/<int:args>', methods=["GET"])
def update(args):

    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    # acquire a lock on the catalog db to update the item
    write_lock.acquire()

    # query the catalog db
    catalog = db.session.query(Book).filter_by(id=args).with_for_update().first()

    # check if the quantity is gt 0
    if catalog is not None and catalog.quantity > 0:

        # update the db, commit and release lock
        catalog.quantity -= 1
        db.session.commit()

        # update the replica
        try:
            replica_url = replica_host + ':' + replica_port + '/update_replica/' + str(args)
            replica_update_request = requests.get(url=replica_url, data={'quantity': catalog.quantity})
        except Exception:
            print('Exception occurred while writing to replica')
        else:
            if replica_update_request.json()['result'] == -1:
                print('Exception occurred while writing to replica')
        finally:
            write_lock.release()

            # return success with remaining stock
            return {'result': 0, 'remaining_stock': catalog.quantity, 'catalog_host/ip': hostname + '/' + ip }

    # quantity == 0, return failure
    else:

        # end db session and release lock
        db.session.commit()
        write_lock.release()

        # return failure
        return {'result': -1, 'catalog_host/ip': hostname + '/' + ip}




# Delete book by item number
@app.route('/book/<id>', methods=['DELETE'])
def delete_book(id):
    book = Book.query.get(id)
    db.session.delete(book)
    db.session.commit()

    return book_schema.jsonify(book)



#needed this function to update replication server of the catalog after updating the original db
@app.route('/update_replica/<int:args>', methods=['GET'])
def update_replica(args):

    try:
        bookk = db.session.query(Book).filter_by(id=args).with_for_update().first()
        bookk.quantity = request.values['quantity']
        db.session.commit()
        print('Replica updated for id: %d' % args)
    except Exception:
        return {'result': -1}
    else:
        return {'result': 0}



@app.route('/', methods=['GET'])
def start():
    return "cat is working!"


if __name__ == '__main__':
    # app.run(debug=True)
    # app.run(host='0.0.0.0', port=5000, debug=True)

    app.run(host=app.config.get("HOST", 'localhost'),
            port=app.config.get("PORT", 5002))
