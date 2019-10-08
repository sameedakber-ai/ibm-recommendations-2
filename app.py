from flask import Flask, request, render_template
from flask_sqlalchemy import SQLAlchemy

from model.recommender import *

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.DateTime, primary_key=True)
    article = db.Column(db.String(150))

    def __repr__(self):
        return '<User %r>' % self.id


@app.route('/')
def helloK_world():
    return render_template('index.html')


@app.route('/signin', methods=['POST', 'GET'])
def signin():
    if request.method == 'POST':
        user_id = int(request.form['userid'])
        if user_id in df.user_id.tolist():
            recommender = Collaborative(df, user_id)
            recs = recommender.make_collaborative_recs(15)
            return render_template('user.html', user_id=user_id, recs=recs)
        else:
            return render_template('newuser.html', user_id=user_id)

@app.route('/article/<int:articleid>')
def show_article_id(article_id):
    if article_id in df.article_id:
        article_content = df[['article_id', 'doc_body']]
        return render_template('article.html', )


@app.route('/notfound')
def notfound():
    return render_template('lost.html')


if __name__ == '__main__':
    app.run(debug=True)
