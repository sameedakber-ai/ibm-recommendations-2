from flask import Flask, request, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

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
def hello_world():
    return render_template('index.html')


@app.route('/signin', methods=['POST', 'GET'])
def signin():
    if request.method == 'POST':
        userid = request.form['userid']



if __name__ == '__main__':
    app.run(debug=True)
