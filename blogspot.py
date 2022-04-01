from email.message import Message
from tokenize import Name
from flask import Flask, render_template, Request, request
from flask_sqlalchemy import SQLAlchemy
import json
from datetime import datetime
local_server = True
with open('blog_config.json', 'r') as c:
    params = json.load(c)["params"]
app = Flask(__name__)
if (local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

db = SQLAlchemy(app)


class Contacts(db.Model):
    Serial_Number = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(12), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12),  nullable=True)
    message = db.Column(db.String(1200),  nullable=False)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/post')
def bootstrap():
    return render_template('post.html')


@app.route('/contact', methods={'GET', 'POST'})
def contact():
    if(request.method == 'POST'):
        '''add entry to the database'''
        Name = request.form.get('Name')
        Phone = request.form.get('Phone')
        Email = request.form.get('Email')
        Message = request.form.get('Message')
        entry = Contacts(name=Name, phone=Phone, email=Email,
                         date=datetime.now(), message=Message)
        db.session.add(entry)
        db.session.commit()
    return render_template('contact.html')


if __name__ == '__main__':
    app.run(debug=True)
