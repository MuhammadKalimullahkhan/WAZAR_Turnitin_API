from flask import jsonify


def missing_arguments():
    return jsonify({"error": "missing arguments"})
