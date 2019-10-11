# Import flask libraries
from flask import Flask, request, render_template, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy

# Import sqlalchemy libraries
from sqlalchemy import desc, sql
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker

# Import miscellaneous libraries
from datetime import  datetime

# Import recommender classes and functions from mode/recommender.py
from model.recommender import *

# Set up engine and Object-relation mapping (ORM) for the sqlite database
engine = create_engine('sqlite:///data/data.db')
md = MetaData(engine)
table = Table('user-article-interactions', md, autoload=True)
Session = sessionmaker(bind=engine)

# Create a fresh session
session = Session()

# Create dataframe from sqlite database
df = pd.read_sql_table('user-article-interactions', engine)

# Initialize flask app
app = Flask(__name__)

#configure sqlite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

# Set global current user id
currentuser = 0

# Create a User class to define columns and types of user database
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.DateTime, primary_key=True)
    article = db.Column(db.String(150))

    def __init__(self, id, time, article):
        self.id = id
        self.time = time
        self.article = article

# Display welcome (index) page
@app.route('/')
def hello_world():
    return render_template('index.html')

# Redirect calls to different routes depending
# on if the user is a new user or returning user
@app.route('/temp', methods=['POST', 'GET'])
def temp():
    if request.method == 'POST':
        user_id = int(request.form['userid'])
        if user_id in df.user_id.tolist():
            return redirect(url_for('welcomeuser', userid=user_id))
        else:
            return redirect(url_for('newuser', userid=user_id))

# Welcome returning user by generating tailored recommendations
# and displaying any recently read (since webapp creation) articles
@app.route('/user-<int:userid>', methods=['POST', 'GET'])
def welcomeuser(userid):

    global currentuser

    currentuser = userid

    if (df.user_id==userid).sum() >= 10:
        # Use collaborative filtering to make recommendations
        recommender = Collaborative(df, userid)
        recs = recommender.make_collaborative_recs(15)
    else:
        # Use content based (NLP) system to make recommendations
        user_articles = df.doc_full_name[df.user_id==userid].unique().tolist()
        recommender = Content(df, userid, user_articles)
        recs = recommender.make_content_recs(15)

    # Query user database to find recently read articles
    recent = User.query.filter_by(id=int(userid)).order_by(desc(User.time)).all()
    rec_art = [rec.article for rec in recent]
    rec_time = [rec.time for rec in recent]
    rec_link = dict()
    for art in rec_art:
        rec_link[art] = df.link[df.doc_full_name==art].tolist()[0]
    rec_link = rec_link.values()
    #rec_link = df.link[df.doc_full_name.isin(rec_art)].drop_duplicates(keep='first').tolist()

    # Get the 5 most recently read articles
    result = list(zip(rec_art, rec_time, rec_link))[:5]
    return render_template('user.html', user_id=userid, recs=recs, result=result)

# Welcome new user by displaying the most popular articles
@app.route('/newuser-<int:userid>', methods=['POST', 'GET'])
def newuser(userid):
    most_popular_articles = get_top_ranked_articles(df, 10)
    return render_template('newuser.html', recs = most_popular_articles, id=userid)

# Update read articles when a user clicks on an article link
@app.route('/<path:subpath>-<int:id>-<article>', methods=['GET', 'POST'])
def updatedatabase(subpath, id, article):

    global df
    id = currentuser

    # Catch typos in article names
    article = article.split(str(id) + '-')
    try:
        article = article[1]
    except:
        article = article[0]

    if article not in df.doc_full_name[df.user_id==id].tolist():
        # Add a new row to both the dataframe and database table
        # to record that the user has read the article
        link = df.link[df.doc_full_name==article].tolist()[0]
        descr = df.doc_description[df.doc_full_name==article].tolist()[0]
        article_id = df.article_id[df.doc_full_name==article].tolist()[0]
        df = df.append({'user_id': id, 'article_id':article_id, 'doc_full_name': article, 'link':link, 'doc_description':descr}, ignore_index=True)

        session.execute(table.insert().values(user_id=id, article_id=article_id, doc_full_name=article, doc_description=descr, link=link))
        session.commit()

    user = User.query.filter_by(id=id).all()
    if article not in [data.article for data in user]:
        # Make a new row in the User database
        time = datetime.now()
        new_entry = User(int(id), time, article)
        db.session.add(new_entry)
        db.session.commit()
    else:
        # Update time to current time
        User.query.filter_by(id=id, article=article).update(dict(time = datetime.now()))
        db.session.commit()

    # Redirect to the article link once both databases are updated
    return redirect(subpath)

# Run server
if __name__ == '__main__':
    app.run(debug=True)
