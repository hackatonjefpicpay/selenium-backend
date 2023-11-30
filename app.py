from flask import Flask, jsonify
from aws_request import get_AWS_status

app = Flask(__name__)


@app.route("/aws/<region>", methods=["GET"])
def get_aws_status_api(region):
    result = get_AWS_status(region)
    return jsonify(result)
