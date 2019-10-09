from flask import Flask, request, render_template, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from datetime import  datetime

from model.recommender import *

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.DateTime, primary_key=True)
    article = db.Column(db.String(150))

    def __init__(self, id, time, article):
        self.id = id
        self.time = time
        self.article = article

@app.route('/')
def hello_world():
    return render_template('index.html')

@app.route('/temp', methods=['POST', 'GET'])
def temp():
    if request.method == 'POST':
        user_id = int(request.form['userid'])
        if user_id in df.user_id.tolist():
            return redirect(url_for('welcomeuser', userid=user_id))
        else:
            return redirect(url_for('newuser', userid=user_id))


@app.route('/user-<int:userid>', methods=['POST', 'GET'])
def welcomeuser(userid):
        recommender = Collaborative(df, userid)
        recs = recommender.make_collaborative_recs(15)
        recent = User.query.filter_by(id=int(userid)).order_by(desc(User.time)).all()
        rec_art = [rec.article for rec in recent]
        rec_time = [rec.time for rec in recent]
        rec_link = df.link[df.doc_full_name.isin(rec_art)].drop_duplicates(keep='first').tolist()
        result = list(zip(rec_art, rec_time, rec_link))[:5]
        return render_template('user.html', user_id=userid, recs=recs, result=result)


@app.route('/newuser-<int:userid>', methods=['POST', 'GET'])
def newuser(userid):
    most_popular_articles = get_top_ranked_articles(10)
    return render_template('newuser.html', recs = most_popular_articles, id=userid)

@app.route('/<path:subpath>-<int:id>-<article>', methods=['GET', 'POST'])
def updatedatabase(subpath, id, article):
    global df
    if article not in df.doc_full_name[df.user_id==id].tolist():
        link = df.link[df.doc_full_name==article].tolist()[0]
        descr = df.doc_description[df.doc_full_name==article].tolist()[0]
        article_id = df.article_id[df.doc_full_name==article].tolist()[0]
        df = df.append({'user_id': id, 'article_id':article_id, 'doc_full_name': article, 'link':link, 'doc_description':descr}, ignore_index=True)
    user = User.query.filter_by(id=id).all()
    if article not in [data.article for data in user]:
        time = datetime.now()
        new_entry = User(int(id), time, article)
        db.session.add(new_entry)
        db.session.commit()
    else:
        User.query.filter_by(id=id, article=article).update(dict(time = datetime.now()))
        db.session.commit()

    return redirect(subpath)

if __name__ == '__main__':
    app.run(debug=True)
