from wtapi import db

# Models
class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_ID = db.Column(db.Integer)
    token = db.Column(db.String(512), unique=True)
    username = db.Column(db.String(35), unique=True)
    enrolled_students = db.Column(db.Integer, default=0)
    students_limit = db.Column(db.Integer, default=500)