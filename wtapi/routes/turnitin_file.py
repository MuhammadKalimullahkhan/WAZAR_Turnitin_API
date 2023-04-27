import datetime
from flask import jsonify, request

from turnitin import submitionManager
from wtapi.cookies import createCookies
from wtapi import app
from wtapi.token import token_required


@app.route('/submit_file/', methods=['POST', 'GET'])
@token_required
def submit_file():
    # try:
        # session_id = request.args.get('sid')
        # file_name = request.args.get("file_name")
        # file_title = request.args.get('file_title')
        # assignment_id = request.args.get("assignment_id")
        # auther_first_name = request.args.get("fname")
        # auther_last_name = request.args.get("lname")
        # file_title = file_title + datetime.datetime.now().strftime(" - %f%S%M%H%d%m%Y")
        # auther = {'fname': auther_first_name, "lname": auther_last_name}

        # data = dict()
        # data['assignment_id']  = assignment_id
        # data['auther']               = auther
        # data['file_title']             = file_title
        # data['file_name']          = file_name
        # # data['file_stream']  = open(data['file_name'], "rb")

        file = request.files.get('file')
        data = request.form.to_dict()

        data['file_stream']        = file.stream
        data['assignment_url']     = f"https://www.turnitin.com/t_inbox.asp?lang=en_us&aid={data['assignment_id']}"
        data['file_title']         = data['file_title'] + datetime.datetime.now().strftime(" - %f%S%M%H%d%m%Y")
        data['auther']             = {"fname": data['auther_fname'], "lname":data['auther_lname']}
        session_id                 = data['session_id']

        x = submitionManager.submitFile(createCookies(session_id), data)

        x['auther'] = data['auther']
        x['file_title'] = data['file_title']
        x['error'] = None
    # except Exception as e:
    #     return jsonify({"error": str(e), "code": 400})

        return jsonify(x)


@app.route('/download_file/', methods=["GET", "POST"])
@token_required
def download_file():
    x = request.get_json()
    y = submitionManager.getPDFLink(createCookies(x['session_id']), x['file_title'], x['assignment_id'])
    return jsonify(y)


@app.route('/file_info/', methods=["GET", "POST"])
@token_required
def file_info():
    x = request.get_json()
    print(x)
    y = submitionManager.generatePaperReport(createCookies(x['session_id']), x['file_title'], x['assignment_id'])
    return jsonify(y)