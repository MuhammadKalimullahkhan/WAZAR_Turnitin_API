import jwt
from functools import wraps
from flask import jsonify, request
from wtapi.models.user import Users
from wtapi import app


def token_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        token = request.args.get('token')

        if not token:
            return jsonify({'message': "missing token"})

        # t = Users.query.filter(Users.token == token).first()

        # if not t:
        #     return jsonify({'error': "not authorized"})

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], ['HS256'])
        except Exception as e:
            print(e)
            return jsonify({'error': "invalid token"})
        return f(*args, **kwargs)

    return decorator
