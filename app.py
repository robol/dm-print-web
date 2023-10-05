#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 

from enum import unique
import tempfile
import cups, os

from flask import Flask, session, request, send_from_directory, send_file, render_template, redirect, url_for
from flask_json import json_response
from flask_session import Session
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from oauthlib.oauth2 import WebApplicationClient
import requests, json
from users import User

app = Flask(__name__, static_folder=None)

app.config['BASIC_AUTH_FORCE'] = True
app.config['JSON_ADD_STATUS'] = False
app.config['JSON_JSONP_OPTIONAL'] = False
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY") or os.urandom(24)
app.config['SESSION_TYPE'] = 'filesystem'

# This is needed behind reverse proxies to avoid oauthlib complaining if the requests arrives 
# over an HTTP connection, instead of an HTTPS one.
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

preferered_scheme = os.environ.get("DM_PRINT_PREFERRED_URL_SCHEME", 'https')

# OAuth 2.0 configuration
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
client = WebApplicationClient(GOOGLE_CLIENT_ID)

# Flask-Login configuration
login_manager = LoginManager()
login_manager.init_app(app)

def user_session_key(user_id):
    """Generate a unique string identifying the user in the current session"""
    return 'users/%s' % user_id

@login_manager.user_loader
def load_user(user_id):
    user_key = user_session_key(user_id)
    if user_key in session:
        return User(json.loads(session[user_key]))
    else:
        return None

# Configuration data: can be stati or given through environment variables
printserver = os.environ.get("DM_PRINT_PRINTSERVER", "printserver.dm.unipi.it")
allowed_printers = os.environ.get("DM_PRINT_ALLOWED_PRINTERS", "cdc11,cdcpp,cdcsd,cdclf,cdcpt,cdc6").split(",")
temporary_file_path = os.environ.get("DM_PRINT_TMPPATH", "/tmp/")
app_directory = os.environ.get("DM_PRINT_APP_DIRECTORY", "dm-print-web/build")

# The .setServer / .setPort calls are reduntant, but are apparently may be needed when the 
# printerserver is outside the local network. See https://github.com/OpenPrinting/pycups/issues/30
cups.setServer(printserver)
cups.setPort(631)
conn = cups.Connection(printserver)

# Session setup
Session(app)

###
# API endpoints
###

@app.route("/getPrinters")
@login_required
def getPrinters():
    printers = [ { **p, "name": k } for k,p in conn.getPrinters().items() if k in allowed_printers ]

    res = json_response(
        status_ = 200,
        printers = printers
    )
    res.headers.add('Access-Control-Allow-Origin', '*')

    return res

@app.route("/printFile", methods = ['POST'])
@login_required
def printFile():
    file = request.files['file']
    filename = file.filename

    if not filename.endswith(".pdf"):
        res = json_response(result = "Only PDF files are allowed", status_ = 403)
    else:
        # Create a temporary folder
        newpath = os.path.join(temporary_file_path, tempfile.mktemp() + ".pdf")
        file.save(newpath)

        # Print the new file?
        printer_name = request.form.get('printer')
        conn.printFile(printer_name, newpath, filename, {})

        os.remove(newpath)

        # Log the print
        print(" * User %s printed %s on %s" % (current_user.email, filename, printer_name))

        res = json_response(
            result = "OK"
        )

    res.headers.add('Access-Control-Allow-Origin', '*')
    return res

@app.route("/userinfo")
def userinfo():
    if current_user.is_authenticated:
        return json_response(user = { 
            'email': current_user.email, 'name': current_user.name, 
            'id': current_user.get_id()
        })
    else:
        return json_response(user = None)

###
# Static web pages and login
###

@app.route("/")
def index():
    if current_user.get_id():
        return send_file(os.path.join(app_directory, 'index.html'))
    else:
        return render_template("login.html")

# Login
def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

@app.route("/login")
def login():
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=url_for('callback', _external = True, _scheme = preferered_scheme),
        scope=["openid", "email", "profile"],
    )

    return redirect(request_uri)


# Login Callback
@app.route("/login/callback")
def callback():
    # Get authorization code Google sent back to you
    code = request.args.get("code")

    result = "<p>code: " + code + "</p>"

    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Prepare and send a request to get tokens! Yay tokens!
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=url_for('callback', _external = True, _scheme = preferered_scheme),
        code=code,
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    # Parse the tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))

    # Now that you have tokens (yay) let's find and hit the URL
    # from Google that gives you the user's profile information,
    # including their Google profile image and email
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # You want to make sure their email is verified.
    # The user authenticated with Google, authorized your
    # app, and now you've verified their email through Google!
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
    else:
        return "User email not available or not verified by Google.", 400

    # Create a user in your db with the information provided by Google
    user = User(unique_id, users_name, users_email, picture)
    session[user_session_key(unique_id)] = user.to_json()

    # Begin user session by logging the user in
    login_user(user)

    # Send user back to homepage
    return redirect(url_for("index"))


# Logout
@app.route("/logout")
@login_required
def logout():
    users.pop(current_user.get_id())
    logout_user()
    return redirect(url_for("index"))        

@app.route("/<path:path>")
def build(path):
    return send_from_directory(app_directory, path)

if __name__ == "__main__":
    print(" * DM-PRINT-WEB 0.1 starting")

    app.run(debug = (os.environ.get("DM_PRINT_DEBUG", "0") == "1"))



