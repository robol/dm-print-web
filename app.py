#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 

import tempfile
import os

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
from printer_service import (
    CupsCallError,
    CupsTimeoutError,
    IsolatedCupsClient,
    PrinterCache,
)

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
OPENID_CLIENT_ID = os.environ.get("OPENID_CLIENT_ID", "")
OPENID_CLIENT_SECRET = os.environ.get("OPENID_CLIENT_SECRET", "")
OPENID_DISCOVERY_URL = os.environ.get("OPENID_DISCOVERY_URL", "")
client = WebApplicationClient(OPENID_CLIENT_ID)

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
printer_refresh_interval = float(os.environ.get("DM_PRINT_REFRESH_INTERVAL", "10"))
printer_refresh_timeout = float(os.environ.get("DM_PRINT_REFRESH_TIMEOUT", "5"))
printer_submission_timeout = float(os.environ.get("DM_PRINT_SUBMISSION_TIMEOUT", "20"))
printer_max_backoff = float(os.environ.get("DM_PRINT_MAX_REFRESH_BACKOFF", "60"))

cups_client = IsolatedCupsClient(
    printserver,
    list_timeout=printer_refresh_timeout,
    print_timeout=printer_submission_timeout,
)
printer_cache = PrinterCache(
    cups_client,
    allowed_printers,
    refresh_interval=printer_refresh_interval,
    max_backoff=printer_max_backoff,
)

# Session setup
Session(app)

###
# API endpoints
###

@app.before_request
def start_printer_cache():
    printer_cache.start()


@app.route("/getPrinters")
@login_required
def getPrinters():
    snapshot = printer_cache.snapshot()

    res = json_response(
        status_ = 200,
        **snapshot
    )
    res.headers.add('Access-Control-Allow-Origin', '*')

    return res

@app.route("/printFile", methods = ['POST'])
@login_required
def printFile():
    file = request.files.get('file')
    if file is None:
        return json_response(result="A PDF file is required", status_=400)

    filename = file.filename

    try:
        options = json.loads(request.form.get('options'))
        if not isinstance(options, dict):
            options = {}
    except (TypeError, json.JSONDecodeError):
        options = {}

    # Make sure option values are strings
    for key in options:
        options[key] = str(options[key])

    if options.get("page-ranges") == "":
        options.pop("page-ranges", None)

    # A few default options that we set here, or that we 
    # may expose in the future. 
    # 
    # For a complete list, see https://github.com/clarkmcc/cloud-print-connector/blob/7dbe9ab13d243e8ad9da1a9ffa1b9032ca115b4d/cups/cups.go#L62
    options["collate"] = "true"

    if not filename.lower().endswith(".pdf"):
        res = json_response(result = "Only PDF files are allowed", status_ = 403)
    else:
        printer_name = request.form.get('printer')
        if printer_name not in allowed_printers:
            res = json_response(result="Printer is not allowed", status_=400)
        else:
            newpath = None
            try:
                with tempfile.NamedTemporaryFile(
                    dir=temporary_file_path, suffix=".pdf", delete=False
                ) as temporary_file:
                    newpath = temporary_file.name
                    file.save(temporary_file)

                job_id = cups_client.print_file(
                    printer_name, newpath, filename, options
                )
                print(
                    " * User %s submitted %s on %s as job %s"
                    % (current_user.email, filename, printer_name, job_id)
                )
                res = json_response(result="OK", job_id=job_id)
            except CupsTimeoutError as exc:
                app.logger.warning("CUPS print submission timed out: %s", exc)
                res = json_response(
                    result=(
                        "The print server did not respond in time. "
                        "The job may have been accepted; please check before retrying."
                    ),
                    status_=504,
                )
            except CupsCallError as exc:
                app.logger.warning("CUPS print submission failed: %s", exc)
                res = json_response(
                    result="The print server is temporarily unavailable",
                    status_=503,
                )
            except Exception:
                app.logger.exception("Unexpected print submission failure")
                res = json_response(
                    result="The print request could not be completed",
                    status_=500,
                )
            finally:
                if newpath is not None:
                    try:
                        os.remove(newpath)
                    except FileNotFoundError:
                        pass

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
def get_openid_provider_cfg():
    return requests.get(OPENID_DISCOVERY_URL).json()

@app.route("/login")
def login():
    # Find out what URL to hit for openid login
    openid_provider_cfg = get_openid_provider_cfg()
    authorization_endpoint = openid_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for OpenID login and provide
    # scopes that let you retrieve user's profile from OpenID
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=url_for('callback', _external = True, _scheme = preferered_scheme),
        scope=["openid", "email", "profile"],
    )

    return redirect(request_uri)


# Login Callback
@app.route("/login/callback")
def callback():
    # Get authorization code OpenID sent back to you
    code = request.args.get("code")

    openid_provider_cfg = get_openid_provider_cfg()
    token_endpoint = openid_provider_cfg["token_endpoint"]

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
        auth=(OPENID_CLIENT_ID, OPENID_CLIENT_SECRET),
    )

    # Parse the tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))

    # Now that you have tokens (yay) let's find and hit the URL
    # from OpenID that gives you the user's profile information,
    # including their OpenID profile image and email
    userinfo_endpoint = openid_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    if userinfo_response.json().get("email"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        users_name = userinfo_response.json()["name"]

    try:
        affiliation_data = json.loads(requests.get("https://manage.dm.unipi.it/api/v0/public/staff?email=%s" % users_email).text)
        affiliation_data = affiliation_data["data"]
    except:
        return "Impossibile controllare le qualifiche dell'utente: riprovare più tardi.", 400

    if 'staff' in affiliation_data and len(affiliation_data['staff']) > 0:
        # Create a user in your db with the information provided by Google
        user = User(unique_id, users_name, users_email)
        session[user_session_key(unique_id)] = user.to_json()

        # Begin user session by logging the user in
        login_user(user)

        # Send user back to homepage
        return redirect(url_for("index"))
    else:        
        return "Questo utente non ha il permesso di accedere a questo servizio, riservato solo a docenti del Dipartimento di Matematica. Per ulteriori informazioni, contatta help@dm.unipi.it.", 400

    


# Logout
@app.route("/logout")
@login_required
def logout():
    session.pop(user_session_key(current_user.get_id()))
    logout_user()
    return redirect(url_for("index"))        

@app.route("/<path:path>")
def build(path):
    return send_from_directory(app_directory, path)

if __name__ == "__main__":
    print(" * DM-PRINT-WEB 0.2 starting")

    print("OPENID CONFIGURATION:")
    print(" - OPENID_CLIENT_ID: %s" % OPENID_CLIENT_ID)
    print(" - OPENID_DISCOVERY_URL: %s" % OPENID_DISCOVERY_URL)

    app.run(debug = (os.environ.get("DM_PRINT_DEBUG", "0") == "1"))

