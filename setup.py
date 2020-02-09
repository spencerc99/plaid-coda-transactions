"""
This file should provide methods to complete authorization with different plaid banks 

maybe through a web interface that stores it into a local file
"""
from flask import Flask
from flask import render_template
from flask import request
from flask import jsonify
from plaid_helpers import client

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.ejs")


# Exchange token flow - exchange a Link public_token for
# an API access_token
# https://plaid.com/docs/#exchange-token-flow
@app.route("/get_access_token", methods=["POST"])
def get_access_token():
    global access_token
    public_token = request.form["public_token"]
    try:
        exchange_response = client.Item.public_token.exchange(public_token)
    except plaid.errors.PlaidError as e:
        return jsonify(format_error(e))

    pretty_print_response(exchange_response)
    access_token = exchange_response["access_token"]
    return jsonify(exchange_response)
