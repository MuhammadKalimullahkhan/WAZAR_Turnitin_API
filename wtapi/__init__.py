import turnitin
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
db = SQLAlchemy()

app.config['SECRET_KEY'] = "!#TET)(\"I{kK249u,,.zm,.SF(*#$Q(MN>lejarfj234ou'A:?SDF{"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///turnitin_api.sqlite'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/wtapi'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['admin_password'] = "!@0345Kalim"


db.init_app(app)
migrate = Migrate(app, db)

# Import Custom Modules
from wtapi.token import token_required
from wtapi.routes.turnitin import *
from wtapi.routes.turnitin_file import *
from wtapi.routes.user import *
from wtapi.cookies import createCookies




@app.route('/', methods=['POST', 'GET'])
def index():
    return "--version: 2.0, it works"


@app.route('/login/', methods=['POST', 'GET'])
# @token_required
def login_page():
    # email    = request.args.get('email')
    # password = request.args.get('password')
    data = request.get_json()
    if not (data): 
        return jsonify({'error': 'missing email or password'}), 403
        
    auth = turnitin.turnitinLogin(data['email'], data['password'])
    if auth: 
        return jsonify({'auth': auth})
    else: 
        return jsonify({'error': 'invalid email or password'})


@app.route('/fresh_login/', methods=['POST', 'GET'])
# @token_required
def fresh_login_page():
    data = request.get_json()
    if not (data): 
        return jsonify({'error': 'missing email or password'}), 403
        
    auth = turnitin.turnitinFreshLogin(data['email'], data['password'])
    if auth: 
        return jsonify({'auth': auth})
    else: 
        return jsonify({'error': 'invalid email or password'})
    

@app.route('/logout/', methods=['GET', 'POST'])
# @token_required
def logout():
    data = request.get_json()
    is_logout = turnitin.turnitinLogout(createCookies(data['sid']))
    return jsonify(error=0, is_logout=is_logout)    

with app.app_context():
    db.create_all()