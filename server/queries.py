from flask import Blueprint, jsonify, request

queries = Blueprint('queries', __name__)

@queries.route('/query',methods=['GET'])
def query():
    return jsonify({"message":"Query"})