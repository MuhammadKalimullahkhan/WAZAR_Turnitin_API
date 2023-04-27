import datetime
from flask import request
import jwt
from wtapi import app, db
from wtapi.models.user import Users

@app.route('/user/create/', methods=['POST', 'GET'])
def home_page():
    admin_password = request.args.get('pass')

    if admin_password == app.config['admin_password']:
        username = request.args.get('user')
        std_limit = request.args.get('limit')
        token = jwt.encode({'user': f"{username} {datetime.datetime.now()}", 'exp': datetime.datetime.utcnow() + datetime.timedelta(days=365)}, app.config['SECRET_KEY'])

        std_limit = int(std_limit) if std_limit else 500
        try:
            std_id = int(datetime.datetime.now().strftime("%Y%d%m%f"))
            user = Users(user_ID=std_id, username=username, token=token, enrolled_students=0, students_limit=std_limit)

            db.session.add(user)
            db.session.commit()
        except Exception as e:
            print(e)
            return {"error": f"{e}"}

        return {"token": token}
    else:
        return {"error": "invalid password", "admin_login":False}


@app.route("/user/<int:user_id>/edit_limit/<int:students_limit>/")
def user_edit_limit(user_id, students_limit):
    admin_password = request.args.get('pass')

    if admin_password == app.config['admin_password']:
        user:Users = Users.query.filter(Users.user_ID == user_id).first()
        user.students_limit = students_limit

        db.session.add(user)
        db.session.commit()
        return f"New Limit: {user.students_limit}"
    return {"status": False, "error":"Invalid/Not provided Password"}


@app.route('/users/<string:password>')
def get_all_users(password):
    if password == app.config['admin_password']:
        users = Users.query.all()
        print(users)
        return [
            {
                "token": user.token,
                "user_ID": user.user_ID,
                "username": user.username,
                "std_enrolled": user.enrolled_students,
                "limit": user.students_limit,
            } for user in users
        ]
    return {"status": False, "error":"Invalid/Not provided Password"}

@app.route('/user/<string:token>/')
def local_user_info(token):
    try:
        user = Users.query.filter(Users.token == token).first()
        return {
            "token": user.token,
            "user_ID": user.user_ID,
            "username": user.username,
            "std_enrolled": user.enrolled_students,
            "limit": user.students_limit,
        }
    except Exception as e:
        print(e)
    return {"error":"invalid token"}


@app.route('/user/<int:token>/')
def local_user_info_id(token):
    try:
        user = Users.query.filter(Users.user_ID == int(token)).first()
        return {
            "token": user.token,
            "user_ID": user.user_ID,
            "username": user.username,
            "std_enrolled": user.enrolled_students,
            "limit": user.students_limit,
        }
    except Exception as e:
        print(e)
    return {"error":"invalid token"}