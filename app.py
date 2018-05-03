#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, redirect, request, session
from flask.json import jsonify
from requests_oauthlib import OAuth2Session

client_id = "akXqj18XcHJveAJB1hEO4L39ceTUPcrPW9zY0Ugu"
client_secret = "Qby5PVS7l08d5B1eRIV981MZx9vbS5rjmVE7djhiA9NWhBHsy5QfTOatet8IMYwncA0mGOKKkntp7ntpMeJjFYL2VbJu2bsZDBNNKY5Z7G036pC5q4q3xLZSR3Xiw2vZ"
authorization_base_url = 'http://localhost:8000/o/authorize'
token_url = 'http://localhost:8000/o/token/'
redirect_uri = "http://localhost:8082/callback"

app = Flask(__name__)
app.config['SECRET_KEY'] = 'qwertyuiop'


# class authorize(MethodView):
#
#     def get(self):
#         # test = client.prepare_token_request(request.url)
#         test = client.prepare_authorization_request(authorization_url="https://localhost:8000/o/authorize", )
#         response = Response()
#         response.data = test
#
#         return response


@app.route("/")
def idx():
    return "123"


@app.route("/login")
def login():
    django = OAuth2Session(client_id)
    authorization_url, state = django.authorization_url(authorization_base_url)

    # State is used to prevent CSRF, keep this for later.
    session['oauth_state'] = state
    print(authorization_url)
    return redirect(authorization_url)


@app.route("/callback", methods=["POST", "GET"])
def callback():
    django = OAuth2Session(client_id, state=session['oauth_state'], redirect_uri=redirect_uri)
    token = django.fetch_token(
        token_url,
        # code=request.values.get("code"),
        client_secret=client_secret,
        authorization_response=request.url,
        verify=False,
    )

    if token.get("access_token"):
        resp = django.get("http://localhost:8000/v1/api/get_user")
        get_user = resp.json()
        return jsonify(get_user)

    return jsonify(token)


# app.add_url_rule("/callback", view_func=authorize.as_view("auth"))

if __name__ == '__main__':
    app.run(port=443, ssl_context=("server.pem", "server.pem"))
