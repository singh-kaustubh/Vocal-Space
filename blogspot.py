from cgi import parse_multipart
import email
from email.message import Message
from tokenize import Name
from unicodedata import name
from django.shortcuts import render
from flask import Flask, render_template, Request, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
import json
from werkzeug.utils import secure_filename
from datetime import datetime
from flask import session
import os
from sqlalchemy import false
import math

local_server = True
with open('blog_config.json', 'r') as c:
    params = json.load(c)["params"]
app = Flask(__name__)
app.secret_key = "Your_secret_string"
app.config['Upload_folder'] = params['upload_location']
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL='TRUE',
    MAIL_USERNAME=params['gmail_user'],
    MAIL_PASSWORD=params['gmail_pass']
)
mail = Mail(app)
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


class Posts(db.Model):
    Serial_Number = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(25),  nullable=False)
    content = db.Column(db.String(1200), nullable=False)
    tagline = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12),  nullable=True)
    img_file = db.Column(db.String(12), nullable=True)


@app.route('/')
def home():
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts)/int(params['no_of_posts']))
    page = request.args.get('page')
    if(not str(page).isnumeric()):
        page = 1
    page = int(page)
    posts = posts[(page-1)*int(params['no_of_posts']):(page-1)
                  * int(params['no_of_posts'])+int(params['no_of_posts'])]  
    if page == 1:
        prev = "#"
        next = "/?page="+str(page+1)
    elif page == last:
        next = "#"
        prev = "/?page="+str(page-1)
    else:
        next = "/?page="+str(page+1)
        prev = "/?page"+str(page-1)
    return render_template('index.html', params=params, posts=posts, prev=prev, next=next)


@app.route('/index')
def index():
    posts = Posts.query.filter_by().all()[0:params['no_of_posts']]
    return render_template('index.html', params=params, posts=posts)


@app.route('/login', methods={'GET', 'POST'})
def adminlogin():
    if ('user' in session and session['user'] == params['admin_id']):
        posts = Posts.query.all()
        return render_template('dashboard.html', params=params, posts=posts)
    if request.method == 'POST':
        username = request.form.get('uname')
        userpass = request.form.get('upass')
        if (username == params['admin_id']) and (userpass == params['admin_pass']):
            session['user'] = username
            return render_template('dashboard.html', params=params)
    else:
        return render_template('login.html', params=params)


@app.route('/about')
def about():
    return render_template('about.html', params=params)


@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html', params=params, post=post)


@app.route('/uploader', methods={'GET', 'POST'})
def uploader():
    if ('user' in session and session['user'] == params['admin_id']):
        if (request.method == 'POST'):
            f = request.files['file1']
            f.save(os.path.join(
                app.config['Upload_folder'], secure_filename(f.filename)))
            return redirect('/index')


@app.route('/logout', methods={'GET', 'POST'})
def logout():
    session.pop('user')
    return redirect('/index')


@app.route("/delete/<string:Serial_Number>", methods={'GET', 'POST'})
def delete(Serial_Number):
    if ('user' in session and session['user'] == params['admin_id']):
        post = Posts.query.filter_by(Serial_Number=Serial_Number).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/index')


@ app.route('/contact', methods={'GET', 'POST'})
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
        mail.send_message(
            f'[New message from coding space] from {Name}',
            sender=Email,
            recipients=[params['gmail_user']],
            body=Message+"\n"+Phone
        )
    return render_template('contact.html', params=params)


@app.route("/edit/<string:Serial_Number>", methods={'GET', 'POST'})
def edit(Serial_Number):
    if ('user' in session and session['user'] == params['admin_id']):
        if (request.method == 'POST'):
            box_title = request.form.get('title')
            box_tagline = request.form.get('tagline')
            box_slug = request.form.get('slug')
            box_img_file = request.form.get('img_file')
            box_content = request.form.get('content')
            date = datetime.now()
            if Serial_Number == '0':
                post = Posts(title=box_title, tagline=box_tagline,
                             slug=box_slug, img_file=box_img_file, date=date, content=box_content)
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(
                    Serial_Number=Serial_Number).first()
                post.title = box_title
                post.tagline = box_tagline
                post.content = box_content
                post.slug = box_slug
                post.img_file = box_img_file
                post.date = date
                db.session.commit()
                return redirect('/edit'+Serial_Number)
        post = Posts.query.filter_by(Serial_Number=Serial_Number).first()
        return render_template('edit.html', params=params, post=post, Serial_Number=Serial_Number)


if __name__ == '__main__':
    app.run(debug=True)
