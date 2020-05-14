from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
import os

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Init db
db = SQLAlchemy(app)
# Init ma
ma = Marshmallow(app)

# book class
class Book(db.Model):
    itemnum = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)
    cost = db.Column(db.Float)
    topic = db.Column(db.String(100))
    name = db.Column(db.String(100), unique=True)

    def __init__(self, quantity, cost, topic, name):
        self.quantity = quantity
        self.cost = cost
        self.topic = topic
        self.name = name

#Schema
class bookschema(ma.Schema):
    class Meta:
        fields = ('itemnum', 'quantity', 'cost', 'topic', 'name')


book_schema = bookschema()
books_schema = bookschema( many=True)

#adding book to the db
@app.route('/book', methods=['POST'])
def add_book():
  quantity = request.json['quantity']
  cost = request.json['cost']
  topic = request.json['topic']
  name = request.json['name']

  new_book = Book(quantity, cost, topic, name)

  db.session.add(new_book)
  db.session.commit()

  return book_schema.jsonify(new_book)



# Get All books
@app.route('/books', methods=['GET'])
def get_books():
  all_books = Book.query.all()
  result = books_schema.dump(all_books)
  return jsonify(result)


# Get Single book by its topic
@app.route('/book/<topic>', methods=['GET'])
def get_book(topic):
  book = Book.query.get(topic)
  return book_schema.jsonify(book)

# Update a book by its item number
@app.route('/book/<itemnum>', methods=['PUT'])
def update_book(itemnum):
  book = Book.query.get(itemnum)
  quantity = request.json['quantity']
  cost = request.json['cost']
  topic = request.json['topic']
  name = request.json['name']

  book.quantity = quantity
  book.name = name
  book.cost = cost
  book.topic = topic


  db.session.commit()

  return book_schema.jsonify(book)


# Delete book by item number
@app.route('/book/<itemnum>', methods=['DELETE'])
def delete_book(itemnum):
  book = Book.query.get(itemnum)
  db.session.delete(book)
  db.session.commit()

  return book_schema.jsonify(book)

@app.route('/', methods=['GET'])
def start():
  return "it's working!"

if __name__ == '__main__':
    #app.run(debug=True)
    #app.run(host='0.0.0.0', port=5000, debug=True)

    app.run(host=app.config.get("HOST", "192.168.1.64"),
    port = app.config.get("PORT", 51814))