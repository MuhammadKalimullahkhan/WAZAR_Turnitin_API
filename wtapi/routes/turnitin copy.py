from flask import jsonify, request
import turnitin
from wtapi import app, db
from wtapi.models.user import Users
from wtapi.token import token_required
from wtapi.error import missing_arguments
from wtapi.cookies import createCookies

@app.route('/create_assignments/', methods=['POST', 'GET'])
@token_required
def create_assignments(): 
    class_index = request.args.get('cno')
    session_id = request.args.get('sid')
    ammount = request.args.get('ammount')
    assignment_duration = request.args.get('duration')
    title = request.args.get('title')

    if not (class_index and session_id and ammount and assignment_duration and title):
        return missing_arguments()
    
    auth = createCookies(session_id)

    return jsonify({
        "result": turnitin.createAssignment(
                auth, 
                int(class_index), 
                int(ammount), 
                int(assignment_duration), 
                title
            )
    })


@app.route('/clear_assignments/', methods=['POST', 'GET'])
@token_required
def clear_assignments():
    class_index = request.args.get('cno')
    session_id = request.args.get('sid')

    if not (class_index and session_id): 
        return missing_arguments()
    turnitin.clearAssignment(createCookies(session_id), int(class_index))
    return jsonify({"result": True})


@app.route('/delete_assignments/', methods=['POST', 'GET'])
# @token_required
def delete_assignments():
    class_index = request.args.get('cno')
    session_id = request.args.get('sid')
    start = request.args.get('start')

    if not (class_index and start and session_id): 
        return missing_arguments()

    turnitin.deleteAssignment(createCookies(session_id), int(class_index), int(start))

    return jsonify({'result': True})


@app.route('/enroll_student/', methods=['POST', 'GET'])
@token_required
def enroll_student():
    class_index = request.args.get('cno')
    session_id = request.args.get('sid')
    fname = request.args.get('fname')
    lname = request.args.get('lname')
    email = request.args.get('email')
    token = request.args.get('token')

    if not (class_index and session_id and fname and lname and email): 
        return missing_arguments()

    user:Users = Users.query.filter(Users.token == token ).first()

    if user.enrolled_students >= user.students_limit:
        return {"error": "student limit has been reached"}

    res = turnitin.enrollStudent(
                createCookies(session_id), 
                int(class_index), 
                {
                    'firstname': fname, 
                    'lastname':lname, 
                    'email':email
                }
            )
    if res == None: return {"error": "student already exists"}
    user.enrolled_students += 1

    db.session.add(user)
    db.session.commit()

    return jsonify({
        'result': res
    })
    

@app.route('/enroll_student_list/', methods=['POST', 'GET'])
@token_required
def enroll_student_list():
    token = request.args.get('token')
    class_index = request.args.get('cno')
    session_id = request.args.get('sid')
    std_no = request.args.get('stdno')
    file = request.files.get('file')

    if not (token and class_index and session_id and std_no and file): 
        return missing_arguments()

    std_no = int(std_no)
    user:Users = Users.query.filter(Users.token == token ).first()

    if user.enrolled_students + std_no >= user.students_limit:
        return {
            "error": "student limit has been reached", 
            "ammount": f"remove {user.enrolled_students + std_no - user.students_limit} students from the file to continue"
        }

    res = turnitin.enrollStudentList(createCookies(session_id), int(class_index), file)

    if res == None: 
        return {"error": "student already exists"}
    user.enrolled_students += std_no

    db.session.add(user)
    db.session.commit()

    return jsonify({
        "result": res
    })  


@app.route('/enrolled_students/', methods=['POST', 'GET'])
@token_required
def enrolled_students():
    class_index = request.args.get('cno')
    session_id = request.args.get('sid')

    if not (class_index and session_id): return missing_arguments()
    
    return jsonify(turnitin.getEnrolledStudents(createCookies(session_id), int(class_index)))


@app.route('/student_action/', methods=['POST', 'GET'])
@token_required
def student_action():
    class_index = request.args.get('cno')
    session_id = request.args.get('sid')
    std_id = request.args.get('stdid')
    action = request.args.get('action')
    token = request.args.get('token')

    if not (class_index and session_id and std_id and action): 
        return missing_arguments()

    is_action_done = turnitin.studentAction(createCookies(session_id), int(class_index), std_id, action) 
    if is_action_done == True and action == "del":
        user = Users.query.filter(Users.token == token).first()
        user.enrolled_students -= 1
        db.session.add(user)
        db.session.commit()
        
    return {
        "result": is_action_done
    }


@app.route('/classes/', methods=['POST', 'GET'])
@token_required
def classes():
    session_id = request.args.get('sid')
    return jsonify(turnitin.turnitinManager.getClasses(createCookies(session_id)))


@app.route('/assignments/', methods=['POST', 'GET'])
# @token_required
def assignments():
    data = request.get_json()

    if not (data): return missing_arguments()

    url = turnitin.turnitinManager.getClasses(createCookies(data['sid']))[int(data['cno'])]['url']
    return jsonify(turnitin.turnitinManager.getAssignments(
        url, 
        createCookies(
        data['sid']
        )
    )
)


@app.route('/user_info/', methods=['POST', 'GET'])
@token_required
def user_info():
    session_id = request.args.get('sid')
    return f"{turnitin.userInfo(createCookies(session_id))}"